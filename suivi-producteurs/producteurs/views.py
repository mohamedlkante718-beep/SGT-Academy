import csv
from datetime import date, timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from . import rapports
from .caisse import bilan_centre, portefeuille_prets
from .forms import ConnexionForm, ValidationForm
from .models import Fiche, LigneEffectif, LigneValeur, Producteur, Responsable, Secteur
from .services import cle, comparer_lignes, debut_semaine, evolution, recapitulatif


def _logo():
    """Adresse du logo : celui envoyé dans l'administration (rubrique « Logo »), sinon un fichier
    static/logo.png ou static/logo.jpg déposé à la main, sinon None."""
    from django.contrib.staticfiles import finders
    from django.templatetags.static import static
    from .models import Parametres
    p = Parametres.objects.first()
    if p and p.logo:
        return p.logo.url
    for nom in ("logo.png", "logo.jpg", "logo.jpeg"):
        if finders.find(nom) or (settings.STATIC_ROOT / nom).exists():
            return static(nom)
    return None


def organisation(request):
    """Nom et logo de la structure pour tous les gabarits."""
    return {"sigle": settings.ORGANISATION_SIGLE, "organisation": settings.ORGANISATION_NOM, "logo": _logo()}


class ConnexionView(auth_views.LoginView):
    template_name = "mobile/connexion.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True


def _date_ou_404(texte):
    try:
        return date.fromisoformat(texte)
    except (TypeError, ValueError):
        raise Http404("Date invalide")


def _responsable(user):
    r = getattr(user, "responsable", None)
    return r if r and r.actif else None


def suivi_requis(vue):
    """Réservé à l'administrateur (tout) et aux responsables (leurs producteurs, en lecture + validation)."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff:
            request.est_admin, request.producteurs_visibles = True, Producteur.objects.all()
        elif _responsable(request.user):
            r = _responsable(request.user)
            request.est_admin, request.producteurs_visibles = False, r.producteurs.all()
        else:
            return redirect("accueil")
        return vue(request, *args, **kwargs)
    return enveloppe


@login_required
def accueil(request):
    if request.user.is_staff or _responsable(request.user):
        return redirect("tableau")
    producteur = getattr(request.user, "producteur", None)
    if producteur is None:
        return render(request, "mobile/sans_producteur.html")
    semaine = debut_semaine()
    fiches = list(producteur.fiches.prefetch_related("valeurs")[:12])
    historique = []
    for i, f in enumerate(fiches):
        prec = fiches[i + 1] if i + 1 < len(fiches) else producteur.fiche_precedente(f.semaine)
        historique.append({"fiche": f, "evo": evolution(prec.total_valeurs if prec else None, f.total_valeurs)})
    return render(request, "mobile/accueil.html", {
        "producteur": producteur,
        "semaine": semaine,
        "fin": semaine + timedelta(days=6),
        "fiche_semaine": producteur.fiches.filter(semaine=semaine).first(),
        "a_corriger": producteur.fiches.filter(statut=Fiche.A_CORRIGER),
        "historique": historique,
    })


# ---------------------------------------------------------------- mobile (producteurs)

def _ligne_de(lignes, produit):
    """Ligne d'une fiche correspondant à un produit (par lien, sinon par libellé pour l'historique)."""
    for l in lignes:
        if l.produit_id == produit.pk:
            return l
    for l in lignes:
        if l.produit_id is None and cle(l.libelle) == cle(produit.nom):
            return l
    return None


def _entier(texte):
    texte = (texte or "").replace(" ", "").replace(" ", "").strip()
    if texte == "":
        return None
    if not texte.isdigit():
        raise ValueError
    return int(texte)


@never_cache
@login_required
def saisie(request, semaine=None):
    producteur = getattr(request.user, "producteur", None)
    if producteur is None:
        return redirect("accueil")

    semaine = debut_semaine(_date_ou_404(semaine) if semaine else None)
    if semaine > debut_semaine() + timedelta(days=7):
        messages.error(request, "On ne peut pas saisir une semaine aussi lointaine.")
        return redirect("accueil")
    fiche = producteur.fiches.filter(semaine=semaine).first()
    precedente = producteur.fiche_precedente(semaine)
    verrouillee = bool(fiche and fiche.statut == Fiche.VALIDEE)

    eff = list(fiche.effectifs.all()) if fiche else []
    val = list(fiche.valeurs.all()) if fiche else []
    peff = list(precedente.effectifs.all()) if precedente else []
    pval = list(precedente.valeurs.all()) if precedente else []

    produits = list(producteur.produits_attribues())
    lignes, erreurs = [], {}
    for p in produits:
        le, lv, pe, pv = _ligne_de(eff, p), _ligne_de(val, p), _ligne_de(peff, p), _ligne_de(pval, p)
        ligne = {"produit": p,
                 "q": le.quantite if le else None, "v": lv.montant if lv else None,
                 "pq": pe.quantite if pe else None, "pv": pv.montant if pv else None,
                 "q_brut": None, "v_brut": None}
        if request.method == "POST" and not verrouillee:
            for champ, actif in (("q", p.compter), ("v", p.valoriser)):
                brut = request.POST.get(f"{champ}_{p.pk}", "")
                ligne[champ + "_brut"] = brut
                if not actif:
                    continue
                try:
                    ligne[champ] = _entier(brut)
                except ValueError:
                    erreurs[f"{champ}_{p.pk}"] = "Nombre entier uniquement"
                    ligne[champ] = None
        ligne["erreur_q"], ligne["erreur_v"] = erreurs.get(f"q_{p.pk}"), erreurs.get(f"v_{p.pk}")
        lignes.append(ligne)

    if request.method == "POST" and not verrouillee and not erreurs:
        with transaction.atomic():
            if fiche is None:
                fiche = Fiche(producteur=producteur, semaine=semaine)
            fiche.observations = request.POST.get("observations", "").strip()
            fiche.statut, fiche.saisie_par = Fiche.SOUMISE, request.user
            fiche.save()
            for l in lignes:
                p = l["produit"]
                for modele, liste, champ, attr in ((LigneEffectif, eff, "q", "quantite"), (LigneValeur, val, "v", "montant")):
                    ancienne = _ligne_de(liste, p)
                    if ancienne:
                        ancienne.delete()
                    if l[champ] is not None:
                        modele.objects.create(fiche=fiche, produit=p, libelle=p.nom, **{attr: l[champ]})
        messages.success(request, f"Fiche de la semaine du {fiche.semaine:%d/%m} envoyée à votre responsable.")
        return redirect("accueil")
    if erreurs:
        messages.error(request, "Certaines cases contiennent autre chose qu'un nombre. Corrigez-les puis enregistrez.")

    groupes = {}
    for l in lignes:
        groupes.setdefault(l["produit"].secteur.nom, []).append(l)
    return render(request, "mobile/saisie.html", {
        "producteur": producteur,
        "fiche": fiche,
        "verrouillee": verrouillee,
        "semaine": semaine,
        "fin": semaine + timedelta(days=6),
        "precedente": precedente,
        "groupes": groupes,
        "observations": request.POST.get("observations") if request.method == "POST" else (fiche.observations if fiche else ""),
        "semaine_precedente": semaine - timedelta(days=7),
        "semaine_suivante": semaine + timedelta(days=7) if semaine < debut_semaine() else None,
    })


@login_required
def saisie_supprimer(request, semaine):
    """Le producteur retire une fiche envoyée par erreur, tant qu'elle n'est pas validée."""
    producteur = getattr(request.user, "producteur", None)
    if producteur is None:
        return redirect("accueil")
    fiche = get_object_or_404(producteur.fiches, semaine=_date_ou_404(semaine))
    if fiche.statut == Fiche.VALIDEE:
        messages.error(request, "Cette fiche est déjà validée : demandez à l'administrateur de la supprimer.")
        return redirect("saisie_semaine", semaine=semaine)
    if request.method == "POST":
        fiche.delete()
        messages.success(request, f"La fiche de la semaine du {fiche.semaine:%d/%m} a été supprimée.")
        return redirect("accueil")
    return render(request, "mobile/confirmer_suppression.html", {"fiche": fiche, "producteur": producteur})


# ---------------------------------------------------------------- web (administrateur et responsables)

@suivi_requis
def tableau(request):
    visibles = request.producteurs_visibles
    semaines = list(Fiche.objects.filter(producteur__in=visibles).order_by("-semaine")
                    .values_list("semaine", flat=True).distinct())
    base = {"onglet": "tableau", "est_admin": request.est_admin}
    if not semaines:
        return render(request, "gestion/tableau.html", {**base, "vide": True})
    choix = request.GET.get("semaine")
    semaine = date.fromisoformat(choix) if choix and choix in {s.isoformat() for s in semaines} else semaines[0]
    producteurs = visibles.filter(actif=True)
    secteurs = Secteur.objects.filter(actif=True, produits__producteurs__in=producteurs).distinct()
    secteur = secteurs.filter(pk=request.GET.get("secteur")).first() if (request.GET.get("secteur") or "").isdigit() else None
    if secteur:
        producteurs = producteurs.filter(produits__secteur=secteur).distinct()
    lignes, tot = recapitulatif(semaine, producteurs)
    a_valider = Fiche.objects.filter(producteur__in=visibles, statut=Fiche.SOUMISE).select_related("producteur")

    if request.GET.get("format") == "csv":
        rep = HttpResponse(content_type="text/csv; charset=utf-8")
        rep["Content-Disposition"] = f'attachment; filename="recapitulatif-ciaf-ce-{semaine}.csv"'
        rep.write("﻿")
        w = csv.writer(rep, delimiter=";")
        w.writerow(["Producteur", "Statut", "Valeur précédente", "Valeur actuelle", "Évolution", "Dépenses", "Ventes",
                    "Résultat net", "Prêts en cours"])
        vide = lambda v: "" if v is None else v
        for l in lignes:
            ecart = l["evo"]["ecart"] if l["evo"] else None
            ligne = [l["producteur"].nom, l["fiche"].get_statut_display() if l["fiche"] else "Non reçue",
                     vide(l["precedent"]), vide(l["actuel"]), vide(ecart),
                     vide(l["depenses"]), vide(l["ventes"]), vide(l["resultat"]), l["prets"]]
            w.writerow(ligne)
        return rep

    points = []
    for s in reversed(semaines[:12]):
        total = sum(f.total_valeurs for f in Fiche.objects.filter(semaine=s, producteur__in=producteurs)
                    .prefetch_related("valeurs"))
        points.append({"semaine": s, "total": total})
    return render(request, "gestion/tableau.html", {
        **base,
        "semaine": semaine,
        "fin": semaine + timedelta(days=6),
        "semaines": [(s, s + timedelta(days=6)) for s in semaines],
        "lignes": lignes,
        "tot": tot,
        "nb_saisies": sum(1 for l in lignes if l["fiche"]),
        "courbe": _courbe(points),
        "secteurs": secteurs,
        "secteur": secteur,
        "a_valider": a_valider,
    })


def _courbe(points):
    """Coordonnées SVG de la courbe ; un seul point s'il n'y a qu'une semaine."""
    if len(points) < 2:
        return {"seul": points[0] if points else None}
    W, H, L, R, T, B = 760, 250, 70, 24, 30, 34
    maxi = max(p["total"] for p in points) * 1.1 or 1
    x = lambda i: L + i * (W - L - R) / (len(points) - 1)
    y = lambda v: T + (H - T - B) * (1 - v / maxi)
    pts = [{"x": round(x(i), 1), "y": round(y(p["total"]), 1), **p} for i, p in enumerate(points)]
    chemin = " ".join(f"{'L' if i else 'M'}{p['x']},{p['y']}" for i, p in enumerate(pts))
    graduations = [{"y": round(y(maxi * k), 1), "v": round(maxi * k / 1000)} for k in (0, .25, .5, .75, 1)]
    return {"W": W, "H": H, "L": L, "R": W - R, "bas": y(0), "points": pts, "chemin": chemin,
            "aire": f"{chemin} L{pts[-1]['x']},{y(0)} L{pts[0]['x']},{y(0)} Z", "graduations": graduations}


@suivi_requis
def fiche_producteur(request, pk):
    producteur = get_object_or_404(request.producteurs_visibles, pk=pk)
    semaines = list(producteur.fiches.values_list("semaine", flat=True))
    choix = request.GET.get("semaine") or request.POST.get("semaine")
    semaine = date.fromisoformat(choix) if choix and choix in {s.isoformat() for s in semaines} else (
        semaines[0] if semaines else None)
    fiche = producteur.fiches.filter(semaine=semaine).first() if semaine else None

    validation = ValidationForm(request.POST or None)
    if request.method == "POST" and fiche:
        if validation.is_valid():
            valider = validation.cleaned_data["decision"] == "valider"
            fiche.statut = Fiche.VALIDEE if valider else Fiche.A_CORRIGER
            fiche.commentaire = validation.cleaned_data["commentaire"].strip()
            fiche.valide_par, fiche.valide_le = request.user, timezone.now()
            fiche.save(update_fields=["statut", "commentaire", "valide_par", "valide_le", "modifie_le"])
            messages.success(request, f"Fiche de {producteur.nom} {'validée' if valider else 'renvoyée pour correction'}.")
            suivante = Fiche.objects.filter(producteur__in=request.producteurs_visibles, statut=Fiche.SOUMISE).first()
            if suivante:
                return redirect(f"{reverse('fiche_producteur', args=[suivante.producteur_id])}?semaine={suivante.semaine}")
            return redirect("tableau")

    precedente = producteur.fiche_precedente(semaine) if semaine else None
    ctx = {"producteur": producteur, "semaines": [(s, s + timedelta(days=6)) for s in semaines],
           "semaine": semaine, "fiche": fiche, "precedente": precedente, "validation": validation,
           "est_admin": request.est_admin,
           "tous": request.producteurs_visibles}
    ctx.update({"prets": producteur.prets.all()[:20], "prets_en_cours": producteur.prets_en_cours()})
    if fiche:
        ctx.update({
            "effectifs": comparer_lignes(fiche.effectifs.all(), precedente.effectifs.all() if precedente else None, "quantite"),
            "valeurs": comparer_lignes(fiche.valeurs.all(), precedente.valeurs.all() if precedente else None, "montant"),
            "evo_total": evolution(precedente.total_valeurs if precedente else None, fiche.total_valeurs),
            "finances_url": reverse("finances", args=[fiche.pk]),
            "correction_url": reverse("admin:producteurs_fiche_change", args=[fiche.pk]),
        })
    return render(request, "gestion/fiche.html", ctx)


# ---------------------------------------------------------------- rapports par période

def _rapport(request):
    """Lit la période et le secteur demandés, puis calcule le rapport sur les producteurs visibles."""
    choix = request.GET.get("periode") or "mois"
    try:
        d = date.fromisoformat(request.GET.get("debut", ""))
        f = date.fromisoformat(request.GET.get("fin", ""))
    except ValueError:
        d = f = None
    if choix == "libre" and not (d and f):
        choix = "mois"
    debut, fin = rapports.bornes(choix, debut=d, fin=f)
    producteurs = request.producteurs_visibles.filter(actif=True)
    secteurs = Secteur.objects.filter(actif=True, produits__producteurs__in=producteurs).distinct()
    secteur = secteurs.filter(pk=request.GET.get("secteur")).first() if (request.GET.get("secteur") or "").isdigit() else None
    if secteur:
        producteurs = producteurs.filter(produits__secteur=secteur).distinct()
    r = rapports.rapport_periode(debut, fin, producteurs)
    r["prets_lignes"], r["prets_tot"] = portefeuille_prets(jusqu_au=fin, producteurs=producteurs)
    if request.est_admin and not secteur:
        r["centre"] = bilan_centre(debut, fin)
    r.update({"choix": choix, "periodes": rapports.PERIODES, "secteurs": secteurs, "secteur": secteur,
              "courbe": _courbe(r["courbe_points"]), "est_admin": request.est_admin, "onglet": "rapport",
              "requete": request.GET.urlencode()})
    return r


@suivi_requis
def rapport(request):
    return render(request, "gestion/rapport.html", _rapport(request))


@suivi_requis
def rapport_imprimable(request):
    r = _rapport(request)
    r["genere_le"] = timezone.localtime()
    r["auteur"] = request.user.first_name or request.user.username
    return render(request, "gestion/rapport_imprimable.html", r)


@suivi_requis
def rapport_excel(request):
    r = _rapport(request)
    contenu = rapports.classeur_excel(r, genere_par=request.user.first_name or request.user.username,
                                      sigle=settings.ORGANISATION_SIGLE, organisation=settings.ORGANISATION_NOM)
    rep = HttpResponse(contenu, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    rep["Content-Disposition"] = f'attachment; filename="rapport-ciaf-ce-{r["debut"]}-au-{r["fin"]}.xlsx"'
    return rep


# ---------------------------------------------------------------- application installable

def manifest(request):
    return JsonResponse({
        "name": f"Suivi des producteurs {settings.ORGANISATION_SIGLE}",
        "short_name": f"Suivi {settings.ORGANISATION_SIGLE}",
        "description": settings.ORGANISATION_NOM,
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f5f7f2",
        "theme_color": "#1f6b45",
        "lang": "fr",
        "icons": [
            {"src": static("icons/icone-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("icons/icone-512.png"), "sizes": "512x512", "type": "image/png"},
            {"src": static("icons/icone-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }, content_type="application/manifest+json")


def service_worker(request):
    return render(request, "sw.js", content_type="application/javascript")
