"""Bilan financier du centre : caisse (entrées et sorties par catégorie), portefeuille de prêts,
et rappel de l'activité déclarée par les producteurs."""

from collections import defaultdict
from datetime import date

from django.db.models import Sum

from .models import CategorieCaisse, Depense, OperationCaisse, Pret, Vente


def portefeuille_prets(jusqu_au=None, producteurs=None):
    """Situation des prêts à une date : prêté, intérêts, remboursé, reste, % remboursé, retards."""
    jusqu_au = jusqu_au or date.today()
    prets = (Pret.objects.filter(type=Pret.TYPE_PRET, date__lte=jusqu_au)
             .select_related("producteur").prefetch_related("remboursements"))
    if producteurs is not None:
        prets = prets.filter(producteur__in=producteurs)
    lignes, t = [], defaultdict(int)
    for p in prets:
        rembourse = sum(r.montant for r in p.remboursements.all() if r.date <= jusqu_au)
        reste = max(p.total_du - rembourse, 0)
        if reste == 0:
            statut = "rembourse"
        elif p.echeance and p.echeance < jusqu_au:
            statut = "retard"
        else:
            statut = "en_cours"
        lignes.append({"pret": p, "rembourse": rembourse, "reste": reste, "statut": statut,
                       "pct": round(min(rembourse / p.total_du * 100, 100), 1) if p.total_du else 0})
        t["capital"] += p.montant
        t["interets"] += p.interets
        t["du"] += p.total_du
        t["rembourse"] += rembourse
        t["reste"] += reste
        t["nb"] += 1
        t["nb_" + statut] += 1
        if statut == "retard":
            t["retard"] += reste
    t["pct_rembourse"] = round(t["rembourse"] / t["du"] * 100, 1) if t["du"] else 0
    t["pct_non_rembourse"] = round(100 - t["pct_rembourse"], 1) if t["du"] else 0
    ordre = {"retard": 0, "en_cours": 1, "rembourse": 2}
    lignes.sort(key=lambda l: (ordre[l["statut"]], l["pret"].producteur.nom, l["pret"].date))
    return lignes, dict(t)


def _flux(debut, fin):
    """Mouvements d'argent du centre entre deux dates (incluses)."""
    ops = OperationCaisse.objects.filter(date__range=(debut, fin)).select_related("categorie")
    entrees = defaultdict(int)
    sorties = defaultdict(int)
    for o in ops:
        (entrees if o.categorie.sens == CategorieCaisse.ENTREE else sorties)[o.categorie.nom] += o.montant
    prets_accordes = Pret.objects.filter(type=Pret.TYPE_PRET, date__range=(debut, fin)).aggregate(s=Sum("montant"))["s"] or 0
    remboursements = Pret.objects.filter(type=Pret.TYPE_REMBOURSEMENT, date__range=(debut, fin)).aggregate(s=Sum("montant"))["s"] or 0
    total_entrees = sum(entrees.values()) + remboursements
    total_sorties = sum(sorties.values()) + prets_accordes
    return {"ops": ops, "entrees": entrees, "sorties": sorties, "prets_accordes": prets_accordes,
            "remboursements": remboursements, "total_entrees": total_entrees, "total_sorties": total_sorties,
            "solde": total_entrees - total_sorties}


def bilan_centre(debut, fin):
    """Tout l'argent du centre sur la période, plus le solde cumulé depuis le début."""
    f = _flux(debut, fin)
    depuis_toujours = _flux(date(2000, 1, 1), fin)

    def detail(dico, total):
        return [{"categorie": k, "montant": v, "pct": round(v / total * 100, 1) if total else 0}
                for k, v in sorted(dico.items(), key=lambda kv: -kv[1])]

    sorties = detail(f["sorties"], f["total_sorties"])
    if f["prets_accordes"]:
        sorties.append({"categorie": "Prêts accordés aux producteurs", "montant": f["prets_accordes"],
                        "pct": round(f["prets_accordes"] / f["total_sorties"] * 100, 1), "pret": True})
    entrees = detail(f["entrees"], f["total_entrees"])
    if f["remboursements"]:
        entrees.append({"categorie": "Remboursements de prêts reçus", "montant": f["remboursements"],
                        "pct": round(f["remboursements"] / f["total_entrees"] * 100, 1), "pret": True})

    # Activité déclarée sur les fiches des producteurs (pour information, hors caisse du centre).
    dep_prod = Depense.objects.filter(fiche__semaine__range=(debut, fin)).aggregate(s=Sum("montant"))["s"] or 0
    ven_prod = Vente.objects.filter(fiche__semaine__range=(debut, fin)).aggregate(s=Sum("montant"))["s"] or 0

    _, portefeuille = portefeuille_prets(jusqu_au=fin)
    return {
        "operations": list(f["ops"]),
        "sorties": sorties, "entrees": entrees,
        "total_sorties": f["total_sorties"], "total_entrees": f["total_entrees"],
        "solde_periode": f["solde"], "solde_cumule": depuis_toujours["solde"],
        "depenses_producteurs": dep_prod, "ventes_producteurs": ven_prod,
        "portefeuille": portefeuille,
    }
