"""Rapport sur une période (mois, trimestre, dates libres) : calcul, puis export Excel.

Une fiche appartient à la période si sa semaine COMMENCE entre la date de début et la date de fin.
La « valeur au début » est celle de la dernière fiche avant la période (à défaut, la première fiche
de la période) ; la « valeur à la fin » est celle de la dernière fiche de la période.
"""

import calendar
from collections import defaultdict
from datetime import date, timedelta
from io import BytesIO

from .models import Depense, Fiche, Pret
from .services import comparer_lignes, evolution

PERIODES = [
    ("mois", "Ce mois-ci"),
    ("mois_precedent", "Le mois dernier"),
    ("trimestre", "Ce trimestre"),
    ("annee", "Cette année"),
    ("libre", "Dates libres"),
]

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]


def bornes(choix, aujourd_hui=None, debut=None, fin=None):
    """Dates de début et de fin d'une période prédéfinie, ou des dates libres données."""
    j = aujourd_hui or date.today()
    if choix == "mois_precedent":
        dernier = j.replace(day=1) - timedelta(days=1)
        return dernier.replace(day=1), dernier
    if choix == "trimestre":
        premier_mois = 3 * ((j.month - 1) // 3) + 1
        d = date(j.year, premier_mois, 1)
        f = date(j.year, premier_mois + 2, calendar.monthrange(j.year, premier_mois + 2)[1])
        return d, f
    if choix == "annee":
        return date(j.year, 1, 1), date(j.year, 12, 31)
    if choix == "libre" and debut and fin:
        return (debut, fin) if debut <= fin else (fin, debut)
    return j.replace(day=1), j.replace(day=calendar.monthrange(j.year, j.month)[1])


def titre_periode(debut, fin):
    if debut.day == 1 and fin == debut.replace(day=calendar.monthrange(debut.year, debut.month)[1]):
        return f"{MOIS[debut.month - 1].capitalize()} {debut.year}"
    return f"Du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}"


def rapport_periode(debut, fin, producteurs):
    """Chiffres de la période pour chaque producteur, plus les totaux et la courbe hebdomadaire."""
    producteurs = list(producteurs.select_related("responsable"))
    fiches = (Fiche.objects.filter(producteur__in=producteurs, semaine__gte=debut, semaine__lte=fin)
              .select_related("producteur")
              .prefetch_related("effectifs__produit", "valeurs__produit", "depenses", "ventes")
              .order_by("semaine"))
    par_producteur = defaultdict(list)
    for f in fiches:
        par_producteur[f.producteur_id].append(f)
    prets = list(Pret.objects.filter(producteur__in=producteurs, date__lte=fin).order_by("date"))

    lignes = []
    tot = defaultdict(int)
    tot["a_debut"] = False
    for p in producteurs:
        fs = par_producteur.get(p.id, [])
        avant = p.fiche_precedente(debut)
        reference = avant or (fs[0] if fs else None)
        derniere = fs[-1] if fs else None
        v_debut = reference.total_valeurs if reference else None
        v_fin = derniere.total_valeurs if derniere else None
        # Sans fiche antérieure et avec une seule fiche dans la période, il n'y a pas encore d'évolution.
        evo = None
        if derniere is not None:
            evo = evolution(None if (reference is derniere) else v_debut, v_fin)
        dep = sum(f.total_depenses for f in fs)
        ven = sum(f.total_ventes for f in fs)
        prets_p = [x for x in prets if x.producteur_id == p.id]
        dans_periode = [x for x in prets_p if x.date >= debut]
        accordes = sum(x.montant for x in dans_periode if x.type == Pret.TYPE_PRET)
        rembourses = sum(x.montant for x in dans_periode if x.type == Pret.TYPE_REMBOURSEMENT)
        encours = sum(x.montant if x.type == Pret.TYPE_PRET else -x.montant for x in prets_p)
        ligne = {
            "producteur": p, "fiches": fs, "nb": len(fs),
            "validees": sum(1 for f in fs if f.statut == Fiche.VALIDEE),
            "reference": reference, "derniere": derniere,
            "debut": v_debut, "fin": v_fin, "evo": evo,
            "depenses": dep, "ventes": ven, "resultat": ven - dep,
            "prets_accordes": accordes, "rembourses": rembourses, "prets_en_cours": encours,
            "prets": dans_periode,
        }
        if derniere is not None:
            ligne["effectifs"] = comparer_lignes(derniere.effectifs.all(),
                                                 None if reference is derniere else reference.effectifs.all(), "quantite")
            ligne["valeurs"] = comparer_lignes(derniere.valeurs.all(),
                                               None if reference is derniere else reference.valeurs.all(), "montant")
        lignes.append(ligne)
        if derniere is not None:
            tot["fin"] += v_fin
            # Un producteur sans fiche antérieure n'a pas de valeur de départ : elle n'entre pas dans le total.
            if reference is not derniere:
                tot["debut"] += v_debut
                tot["a_debut"] = True
        for k in ("nb", "validees", "depenses", "ventes", "prets_accordes", "rembourses", "prets_en_cours"):
            tot[k] += ligne[k]
    tot["resultat"] = tot["ventes"] - tot["depenses"]
    tot["evo"] = evolution(tot["debut"] if tot["a_debut"] else None, tot["fin"]) if tot["fin"] or tot["nb"] else None

    semaines = defaultdict(int)
    for f in fiches:
        semaines[f.semaine] += f.total_valeurs
    depenses_cat = defaultdict(int)
    for d in Depense.objects.filter(fiche__in=fiches):
        depenses_cat[d.get_categorie_display()] += d.montant

    return {
        "debut": debut, "fin": fin, "titre": titre_periode(debut, fin),
        "lignes": lignes, "tot": dict(tot),
        "courbe_points": [{"semaine": s, "total": v} for s, v in sorted(semaines.items())],
        "depenses_par_categorie": sorted(depenses_cat.items()),
        "nb_producteurs": len(producteurs),
        "nb_avec_fiche": sum(1 for l in lignes if l["nb"]),
    }


# ---------------------------------------------------------------- export Excel

def classeur_excel(r, genere_par=""):
    """Classeur .xlsx dans l'esprit du fichier CIAF : récapitulatif, une feuille par producteur,
    puis les feuilles des dépenses, des ventes, des prêts et le bilan financier."""
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    VERT, ROUGE, ENTETE = "1F6B45", "B4322A", "E2EFE6"
    gras = Font(bold=True)
    titre = Font(bold=True, size=14, color=VERT)
    fond_entete = PatternFill("solid", fgColor=ENTETE)
    trait = Side(style="thin", color="D9E0D6")
    bord = Border(top=trait, bottom=trait, left=trait, right=trait)
    nombre = "#,##0"
    pct = "0.0%"

    wb = Workbook()

    def entete(ws, ligne, valeurs):
        for c, v in enumerate(valeurs, start=1):
            cell = ws.cell(ligne, c, v)
            cell.font, cell.fill, cell.border = gras, fond_entete, bord
            cell.alignment = Alignment(wrap_text=True, vertical="center")

    def largeurs(ws, tailles):
        for i, t in enumerate(tailles, start=1):
            ws.column_dimensions[get_column_letter(i)].width = t

    def bandeau(ws, texte):
        ws["A1"] = texte
        ws["A1"].font = titre
        ws["A2"] = f"Période : {r['titre']} (semaines commençant du {r['debut']:%d/%m/%Y} au {r['fin']:%d/%m/%Y})"
        ws["A3"] = f"Généré le {date.today():%d/%m/%Y}" + (f" par {genere_par}" if genere_par else "")
        ws["A2"].font = ws["A3"].font = Font(italic=True, color="5D6B60")

    # --- Récapitulatif
    ws = wb.active
    ws.title = "Récapitulatif"
    bandeau(ws, "Suivi des producteurs CIAF — Récapitulatif")
    cols = ["Producteur", "Responsable", "Fiches reçues", "Fiches validées", "Valeur au début (F)",
            "Valeur à la fin (F)", "Évolution (F)", "Évolution (%)", "Dépenses (F)", "Ventes (F)",
            "Résultat net (F)", "Prêts accordés (F)", "Remboursements (F)", "Prêts en cours (F)"]
    entete(ws, 5, cols)
    premiere = 6
    for i, l in enumerate(r["lignes"]):
        n = premiere + i
        sans_ref = l["reference"] is l["derniere"]
        ws.append([
            l["producteur"].nom, l["producteur"].responsable.nom if l["producteur"].responsable else "",
            l["nb"], l["validees"],
            None if (l["debut"] is None or sans_ref) else l["debut"], l["fin"],
            f'=IF(OR(E{n}="",F{n}=""),"",F{n}-E{n})', f'=IF(OR(E{n}="",E{n}=0,F{n}=""),"",(F{n}-E{n})/E{n})',
            l["depenses"], l["ventes"], f"=J{n}-I{n}",
            l["prets_accordes"], l["rembourses"], l["prets_en_cours"],
        ])
    derniere = premiere + len(r["lignes"]) - 1
    total = derniere + 1
    ws.cell(total, 1, "Total").font = gras
    for c in range(3, 15):
        lettre = get_column_letter(c)
        if lettre == "H":
            ws.cell(total, c, f'=IF(OR(E{total}=0,F{total}=""),"",(F{total}-E{total})/E{total})')
        elif lettre == "G":
            ws.cell(total, c, f"=F{total}-E{total}")
        elif lettre == "K":
            ws.cell(total, c, f"=J{total}-I{total}")
        else:
            ws.cell(total, c, f"=SUM({lettre}{premiere}:{lettre}{derniere})")
        ws.cell(total, c).font = gras
    for ligne in ws.iter_rows(min_row=premiere, max_row=total, min_col=1, max_col=len(cols)):
        for cell in ligne:
            cell.border = bord
            cell.number_format = pct if cell.column_letter == "H" else nombre
    plage = f"G{premiere}:H{total}"
    ws.conditional_formatting.add(plage, CellIsRule(operator="greaterThan", formula=["0"], font=Font(color=VERT, bold=True)))
    ws.conditional_formatting.add(plage, CellIsRule(operator="lessThan", formula=["0"], font=Font(color=ROUGE, bold=True)))
    ws.conditional_formatting.add(f"K{premiere}:K{total}", CellIsRule(operator="lessThan", formula=["0"], font=Font(color=ROUGE)))
    largeurs(ws, [28, 18, 9, 9, 15, 15, 14, 11, 13, 13, 14, 14, 15, 14])
    ws.freeze_panes = "B6"

    # --- Une feuille par producteur
    noms_pris = set(wb.sheetnames)
    for l in r["lignes"]:
        p = l["producteur"]
        nom = "".join(c for c in p.nom if c not in r'[]:*?/\\')[:31] or f"Producteur {p.pk}"
        base, k = nom, 2
        while nom in noms_pris:
            nom = f"{base[:28]} {k}"
            k += 1
        noms_pris.add(nom)
        ws = wb.create_sheet(nom)
        bandeau(ws, p.nom)
        fs = l["fiches"]
        n = 5
        if not fs:
            ws.cell(n, 1, "Aucune fiche reçue sur la période.")
        else:
            semaines = [f"Du {f.semaine:%d/%m}" for f in fs]
            for titre_bloc, attr, champ in (("Quantités", "effectifs", "quantite"), ("Valeur des productions (F CFA)", "valeurs", "montant")):
                ws.cell(n, 1, titre_bloc).font = Font(bold=True, color=VERT, size=12)
                n += 1
                entete(ws, n, ["Produit"] + semaines + ["Évolution"])
                n += 1
                libelles = []
                for f in fs:
                    for x in getattr(f, attr).all():
                        if x.libelle not in libelles:
                            libelles.append(x.libelle)
                debut_bloc = n
                for lib in libelles:
                    ws.cell(n, 1, lib).border = bord
                    for j, f in enumerate(fs, start=2):
                        val = next((getattr(x, champ) for x in getattr(f, attr).all() if x.libelle == lib), None)
                        c = ws.cell(n, j, val)
                        c.number_format, c.border = nombre, bord
                    if len(fs) > 1:
                        a, b = get_column_letter(2), get_column_letter(len(fs) + 1)
                        c = ws.cell(n, len(fs) + 2, f'=IF(OR({a}{n}="",{b}{n}=""),"",{b}{n}-{a}{n})')
                        c.number_format, c.border = nombre, bord
                    n += 1
                if champ == "montant" and libelles:
                    ws.cell(n, 1, "Total des valeurs").font = gras
                    for j in range(2, len(fs) + 2):
                        lettre = get_column_letter(j)
                        c = ws.cell(n, j, f"=SUM({lettre}{debut_bloc}:{lettre}{n - 1})")
                        c.font, c.number_format = gras, nombre
                    n += 1
                n += 1
            ws.cell(n, 1, "Observations").font = Font(bold=True, color=VERT, size=12)
            n += 1
            for f in fs:
                ws.cell(n, 1, f"Semaine du {f.semaine:%d/%m/%Y} ({f.get_statut_display().lower()})")
                ws.cell(n, 2, f.observations or "—").alignment = Alignment(wrap_text=True, vertical="top")
                ws.merge_cells(start_row=n, start_column=2, end_row=n, end_column=max(6, len(fs) + 2))
                n += 1
            n += 1
        ws.cell(n, 1, "Bilan financier").font = Font(bold=True, color=VERT, size=12)
        n += 1
        for lib, val in (("Total dépenses", l["depenses"]), ("Total ventes", l["ventes"]),
                         ("Résultat net (ventes − dépenses)", l["resultat"]),
                         ("Prêts accordés sur la période", l["prets_accordes"]),
                         ("Remboursements reçus sur la période", l["rembourses"]),
                         ("Prêts en cours à la fin", l["prets_en_cours"])):
            ws.cell(n, 1, lib)
            ws.cell(n, 2, val).number_format = nombre
            n += 1
        largeurs(ws, [32] + [13] * (len(fs) + 1))

    # --- Dépenses, ventes, prêts : une ligne par opération
    def feuille_operations(titre_feuille, colonnes, rangees, col_montant, tailles):
        ws = wb.create_sheet(titre_feuille)
        bandeau(ws, f"Suivi des producteurs CIAF — {titre_feuille}")
        entete(ws, 5, colonnes)
        if not rangees:
            ws.cell(6, 1, "Aucune opération sur la période.").font = Font(italic=True, color="5D6B60")
            largeurs(ws, tailles)
            return
        for rangee in rangees:
            ws.append(rangee)
        fin_l = 5 + len(rangees)
        ws.cell(fin_l + 1, 1, "Total").font = gras
        lettre = get_column_letter(col_montant)
        c = ws.cell(fin_l + 1, col_montant, f"=SUM({lettre}6:{lettre}{fin_l})")
        c.font = gras
        for ligne in ws.iter_rows(min_row=6, max_row=fin_l + 1, min_col=1, max_col=len(colonnes)):
            for cell in ligne:
                cell.border = bord
                if isinstance(cell.value, (int, float)) or str(cell.value).startswith("=SUM"):
                    cell.number_format = nombre
                if hasattr(cell.value, "year"):
                    cell.number_format = "dd/mm/yyyy"
        largeurs(ws, tailles)
        ws.freeze_panes = "A6"

    fiches = [f for l in r["lignes"] for f in l["fiches"]]
    feuille_operations(
        "Dépenses",
        ["Producteur", "Date", "Catégorie", "Description", "Quantité", "Prix unitaire (F)", "Montant (F)", "Paiement"],
        [[f.producteur.nom, d.date, d.get_categorie_display(), d.description,
          float(d.quantite) if d.quantite is not None else None, d.prix_unitaire, d.montant, d.get_mode_paiement_display()]
         for f in fiches for d in f.depenses.all()],
        7, [26, 12, 24, 34, 10, 14, 14, 14])
    feuille_operations(
        "Ventes",
        ["Producteur", "Date", "Catégorie / lot", "Description", "Poids", "Quantité", "Prix unitaire (F)", "Montant (F)",
         "Paiement", "Client / remarque"],
        [[f.producteur.nom, v.date, v.categorie, v.description, v.poids,
          float(v.quantite) if v.quantite is not None else None, v.prix_unitaire, v.montant,
          v.get_mode_paiement_display(), v.client]
         for f in fiches for v in f.ventes.all()],
        8, [26, 12, 20, 30, 10, 10, 14, 14, 14, 24])
    feuille_operations(
        "Prêts",
        ["Producteur", "Date", "Type", "Description", "Montant (F)"],
        [[l["producteur"].nom, x.date, x.get_type_display(), x.description,
          x.montant if x.type == Pret.TYPE_PRET else -x.montant] for l in r["lignes"] for x in l["prets"]],
        5, [26, 12, 24, 34, 14])

    # --- Bilan financier
    ws = wb.create_sheet("Bilan financier")
    bandeau(ws, "Suivi des producteurs CIAF — Bilan financier")
    entete(ws, 5, ["Rubrique", "Montant (F CFA)"])
    n = 6
    ws.cell(n, 1, "1. Entrées d'argent (ventes)").font = gras
    ws.cell(n, 2, r["tot"]["ventes"]).number_format = nombre
    n += 1
    ws.cell(n, 1, "2. Sorties d'argent (dépenses)").font = gras
    ws.cell(n, 2, r["tot"]["depenses"]).number_format = nombre
    n += 1
    for cat, montant in r["depenses_par_categorie"]:
        ws.cell(n, 1, f"    dont {cat}")
        ws.cell(n, 2, montant).number_format = nombre
        n += 1
    ws.cell(n, 1, "Résultat net (entrées − sorties)").font = gras
    c = ws.cell(n, 2, "=B6-B7")  # B6 : ventes, B7 : dépenses
    c.font, c.number_format = gras, nombre
    n += 2
    for lib, val in (("Prêts accordés sur la période", r["tot"]["prets_accordes"]),
                     ("Remboursements reçus sur la période", r["tot"]["rembourses"]),
                     ("Prêts en cours à la fin de la période", r["tot"]["prets_en_cours"]),
                     ("Valeur totale des productions à la fin", r["tot"].get("fin", 0))):
        ws.cell(n, 1, lib)
        ws.cell(n, 2, val).number_format = nombre
        n += 1
    largeurs(ws, [42, 18])

    sortie = BytesIO()
    wb.save(sortie)
    return sortie.getvalue()
