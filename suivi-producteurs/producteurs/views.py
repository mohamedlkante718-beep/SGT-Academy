import csv
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from .forms import ConnexionForm, FicheForm, formsets
from .models import Fiche, Producteur, Secteur
from .services import comparer_lignes, debut_semaine, evolution, recapitulatif


class ConnexionView(auth_views.LoginView):
    template_name = "mobile/connexion.html"
    authentication_form = ConnexionForm
    redirect_authenticated_user = True


def _date_ou_404(texte):
    try:
        return date.fromisoformat(texte)
    except (TypeError, ValueError):
        raise Http404("Date invalide")


# ---------------------------------------------------------------- mobile (producteurs)

@login_required
def accueil(request):
    if request.user.is_staff:
        return redirect("tableau")
    producteur = getattr(request.user, "producteur", None)
    if producteur is None:
        return render(request, "mobile/sans_producteur.html")
    semaine = debut_semaine()
    fiches = list(producteur.fiches.prefetch_related("valeurs", "depenses", "ventes")[:12])
    historique = []
    for i, f in enumerate(fiches):
        prec = fiches[i + 1] if i + 1 < len(fiches) else producteur.fiche_precedente(f.semaine)
        historique.append({"fiche": f, "evo": evolution(prec.total_valeurs if prec else None, f.total_valeurs)})
    return render(request, "mobile/accueil.html", {
        "producteur": producteur,
        "semaine": semaine,
        "fin": semaine + timedelta(days=6),
        "fiche_semaine": producteur.fiches.filter(semaine=semaine).first(),
        "historique": historique,
    })


@never_cache
@login_required
def saisie(request, semaine=None):
    producteur = getattr(request.user, "producteur", None)
    if producteur is None:
        if request.user.is_staff:
            messages.info(request, "Les administrateurs modifient les fiches depuis l'administration.")
            return redirect("admin:producteurs_fiche_changelist")
        return render(request, "mobile/sans_producteur.html")

    semaine = debut_semaine(_date_ou_404(semaine) if semaine else None)
    if semaine > debut_semaine() + timedelta(days=7):
        messages.error(request, "On ne peut pas saisir une semaine aussi lointaine.")
        return redirect("accueil")
    fiche = producteur.fiches.filter(semaine=semaine).first()
    precedente = producteur.fiche_precedente(semaine)
    nouvelle = fiche is None
    if nouvelle:
        fiche = Fiche(producteur=producteur, semaine=semaine)

    # Une nouvelle fiche reprend les éléments de la fiche précédente : il ne reste qu'à mettre les chiffres.
    init_eff = [{"libelle": l.libelle} for l in precedente.effectifs.all()] if (nouvelle and precedente) else []
    init_val = [{"libelle": l.libelle} for l in precedente.valeurs.all()] if (nouvelle and precedente) else []
    fabriques = formsets(extra_effectifs=len(init_eff) or (1 if nouvelle else 0),
                         extra_valeurs=len(init_val) or (1 if nouvelle else 0))
    initials = {"effectifs": init_eff, "valeurs": init_val}

    data = request.POST if request.method == "POST" else None
    form = FicheForm(data, instance=fiche)
    jeux = {nom: fab(data, instance=fiche, prefix=nom, initial=initials[nom] or None)
            for nom, fab in fabriques.items()}

    if request.method == "POST" and form.is_valid() and all(j.is_valid() for j in jeux.values()):
        with transaction.atomic():
            fiche = form.save(commit=False)
            fiche.saisie_par = request.user
            fiche.save()
            for j in jeux.values():
                j.instance = fiche
                j.save()
        messages.success(request, f"Fiche de la semaine du {fiche.semaine:%d/%m} enregistrée.")
        return redirect("accueil")

    # Produits proposés, regroupés par secteur, pour la liste « Ajouter un produit ».
    groupes, unites = {}, {}
    for pr in producteur.produits_proposes():
        groupes.setdefault(pr.secteur.nom, []).append(pr)
        unites[pr.nom] = pr.unite
    prec_eff = {l.libelle: l.quantite for l in precedente.effectifs.all()} if precedente else {}
    prec_val = {l.libelle: l.montant for l in precedente.valeurs.all()} if precedente else {}
    return render(request, "mobile/saisie.html", {
        "producteur": producteur,
        "fiche": fiche,
        "nouvelle": nouvelle,
        "semaine": semaine,
        "fin": semaine + timedelta(days=6),
        "precedente": precedente,
        "prec_eff": prec_eff,
        "prec_val": prec_val,
        "form": form,
        "jeux": jeux,
        "groupes": groupes,
        "unites": unites,
        "semaine_precedente": semaine - timedelta(days=7),
        "semaine_suivante": semaine + timedelta(days=7) if semaine < debut_semaine() else None,
    })


# ---------------------------------------------------------------- web (administrateur)

def _semaines():
    return list(Fiche.objects.order_by("-semaine").values_list("semaine", flat=True).distinct())


@staff_member_required
def tableau(request):
    semaines = _semaines()
    if not semaines:
        return render(request, "gestion/tableau.html", {"vide": True})
    choix = request.GET.get("semaine")
    semaine = date.fromisoformat(choix) if choix and choix in {s.isoformat() for s in semaines} else semaines[0]
    producteurs = Producteur.objects.filter(actif=True).prefetch_related("secteurs")
    secteurs = Secteur.objects.filter(actif=True)
    secteur = secteurs.filter(pk=request.GET.get("secteur")).first() if (request.GET.get("secteur") or "").isdigit() else None
    if secteur:
        producteurs = producteurs.filter(secteurs=secteur)
    lignes, tot = recapitulatif(semaine, producteurs)

    if request.GET.get("format") == "csv":
        rep = HttpResponse(content_type="text/csv; charset=utf-8")
        rep["Content-Disposition"] = f'attachment; filename="recapitulatif-ciaf-{semaine}.csv"'
        rep.write("﻿")
        w = csv.writer(rep, delimiter=";")
        w.writerow(["Producteur", "Valeur précédente", "Valeur actuelle", "Évolution", "Dépenses", "Ventes",
                    "Résultat net", "Prêts en cours"])
        for l in lignes:
            ecart = l["evo"]["ecart"] if l["evo"] else None
            w.writerow([l["producteur"].nom, l["precedent"] if l["precedent"] is not None else "",
                        l["actuel"] if l["actuel"] is not None else "", ecart if ecart is not None else "",
                        l["depenses"] if l["depenses"] is not None else "",
                        l["ventes"] if l["ventes"] is not None else "",
                        l["resultat"] if l["resultat"] is not None else "", l["prets"]])
        return rep

    # Courbe de la valeur totale, semaine par semaine (12 dernières semaines).
    points = []
    for s in reversed(semaines[:12]):
        total = sum(f.total_valeurs for f in Fiche.objects.filter(semaine=s, producteur__in=producteurs).prefetch_related("valeurs"))
        points.append({"semaine": s, "total": total})
    return render(request, "gestion/tableau.html", {
        "semaine": semaine,
        "fin": semaine + timedelta(days=6),
        "semaines": [(s, s + timedelta(days=6)) for s in semaines],
        "lignes": lignes,
        "tot": tot,
        "nb_saisies": sum(1 for l in lignes if l["fiche"]),
        "courbe": _courbe(points),
        "onglet": "tableau",
        "secteurs": secteurs,
        "secteur": secteur,
    })


def _courbe(points):
    """Coordonnées SVG de la courbe ; None s'il y a moins de deux semaines."""
    if len(points) < 2:
        return {"seul": points[0] if points else None}
    W, H, L, R, T, B = 760, 240, 70, 20, 16, 34
    maxi = max(p["total"] for p in points) * 1.1 or 1
    x = lambda i: L + i * (W - L - R) / (len(points) - 1)
    y = lambda v: T + (H - T - B) * (1 - v / maxi)
    pts = [{"x": round(x(i), 1), "y": round(y(p["total"]), 1), **p} for i, p in enumerate(points)]
    chemin = " ".join(f"{'L' if i else 'M'}{p['x']},{p['y']}" for i, p in enumerate(pts))
    graduations = [{"y": round(y(maxi * k), 1), "v": round(maxi * k / 1000)} for k in (0, .25, .5, .75, 1)]
    return {"W": W, "H": H, "L": L, "R": W - R, "bas": y(0), "points": pts, "chemin": chemin,
            "aire": f"{chemin} L{pts[-1]['x']},{y(0)} L{pts[0]['x']},{y(0)} Z", "graduations": graduations}


@staff_member_required
def fiche_producteur(request, pk):
    producteur = get_object_or_404(Producteur, pk=pk)
    semaines = list(producteur.fiches.values_list("semaine", flat=True))
    choix = request.GET.get("semaine")
    semaine = date.fromisoformat(choix) if choix and choix in {s.isoformat() for s in semaines} else (
        semaines[0] if semaines else None)
    fiche = producteur.fiches.filter(semaine=semaine).first() if semaine else None
    precedente = producteur.fiche_precedente(semaine) if semaine else None
    ctx = {"producteur": producteur, "semaines": [(s, s + timedelta(days=6)) for s in semaines],
           "semaine": semaine, "fiche": fiche, "precedente": precedente,
           "prets": producteur.prets.all()[:20],
           "prets_en_cours": producteur.prets_en_cours(),
           "tous": Producteur.objects.all()}
    if fiche:
        ctx.update({
            "effectifs": comparer_lignes(fiche.effectifs.all(), precedente.effectifs.all() if precedente else None, "quantite"),
            "valeurs": comparer_lignes(fiche.valeurs.all(), precedente.valeurs.all() if precedente else None, "montant"),
            "evo_total": evolution(precedente.total_valeurs if precedente else None, fiche.total_valeurs),
            "admin_url": reverse("admin:producteurs_fiche_change", args=[fiche.pk]),
        })
    return render(request, "gestion/fiche.html", ctx)


# ---------------------------------------------------------------- application installable

def manifest(request):
    from django.http import JsonResponse
    from django.templatetags.static import static
    return JsonResponse({
        "name": "Suivi producteurs CIAF",
        "short_name": "Suivi CIAF",
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
