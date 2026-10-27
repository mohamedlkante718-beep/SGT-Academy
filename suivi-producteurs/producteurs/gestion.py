"""Pages de gestion de l'administrateur, dans le même style que le tableau de bord :
producteurs, responsables, secteurs et produits, dépenses et ventes d'une fiche, prêts, caisse du centre."""

from datetime import date
from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.db import transaction
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import rapports
from .caisse import bilan_centre, portefeuille_prets
from .forms import (DepensesFormSet, OperationCaisseForm, PretForm, ProducteurAdminForm, ProduitsFormSet,
                    RemboursementForm, ResponsableAdminForm, SecteurForm, VentesFormSet)
from .models import Fiche, OperationCaisse, Pret, Producteur, Responsable, Secteur


def admin_requis(vue):
    """Réservé à l'administrateur ; un responsable est renvoyé vers ses producteurs."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            return redirect("tableau")
        return vue(request, *args, **kwargs)
    return enveloppe


def _page(request, gabarit, onglet, **ctx):
    return render(request, gabarit, {"est_admin": True, "onglet": onglet, **ctx})


# ---------------------------------------------------------------- producteurs

@admin_requis
def producteurs(request):
    liste = (Producteur.objects.select_related("responsable", "utilisateur")
             .prefetch_related("produits__secteur")
             .annotate(nb_fiches=Count("fiches"), derniere=Max("fiches__semaine"),
                       a_valider=Count("fiches", filter=Q(fiches__statut=Fiche.SOUMISE))))
    for p in liste:
        p.liste_secteurs = sorted({pr.secteur.nom for pr in p.produits.all()})
        p.sans_acces = not (p.utilisateur and p.utilisateur.has_usable_password()) or p.telephone.startswith("A-COMPLETER")
    return _page(request, "gestion/producteurs.html", "producteurs", producteurs=liste)


@admin_requis
def producteur_form(request, pk=None):
    producteur = get_object_or_404(Producteur, pk=pk) if pk else None
    form = ProducteurAdminForm(request.POST or None, instance=producteur)
    if request.method == "POST" and form.is_valid():
        producteur = form.save()
        messages.success(request, f"{producteur.nom} enregistré.")
        return redirect("producteurs")
    return _page(request, "gestion/formulaire.html", "producteurs", form=form,
                 titre=f"Modifier {producteur.nom}" if producteur else "Ajouter un producteur",
                 retour=reverse("producteurs"),
                 aide="Cochez les produits que ce producteur remplira sur son téléphone. Il se connecte avec "
                      "son numéro et son code PIN.")


# ---------------------------------------------------------------- responsables

@admin_requis
def responsables(request):
    liste = Responsable.objects.prefetch_related("producteurs").annotate(
        a_valider=Count("producteurs__fiches", filter=Q(producteurs__fiches__statut=Fiche.SOUMISE)))
    return _page(request, "gestion/responsables.html", "responsables", responsables=liste)


@admin_requis
def responsable_form(request, pk=None):
    responsable = get_object_or_404(Responsable, pk=pk) if pk else None
    form = ResponsableAdminForm(request.POST or None, instance=responsable)
    if request.method == "POST" and form.is_valid():
        responsable = form.save()
        messages.success(request, f"{responsable.nom} enregistré.")
        return redirect("responsables")
    return _page(request, "gestion/formulaire.html", "responsables", form=form,
                 titre=f"Modifier {responsable.nom}" if responsable else "Ajouter un responsable",
                 retour=reverse("responsables"),
                 aide="Le responsable se connecte avec son numéro et son code PIN. Il voit uniquement les "
                      "producteurs cochés et valide leurs fiches, sans pouvoir les modifier.")


# ---------------------------------------------------------------- secteurs et produits

@admin_requis
def secteurs(request):
    liste = Secteur.objects.annotate(nb_produits=Count("produits", filter=Q(produits__actif=True)),
                                     nb_producteurs=Count("produits__producteurs", distinct=True))
    return _page(request, "gestion/secteurs.html", "secteurs", secteurs=liste)


@admin_requis
def secteur_form(request, pk=None):
    secteur = get_object_or_404(Secteur, pk=pk) if pk else Secteur()
    form = SecteurForm(request.POST or None, instance=secteur)
    produits = ProduitsFormSet(request.POST or None, instance=secteur, prefix="produits")
    if request.method == "POST" and form.is_valid() and produits.is_valid():
        with transaction.atomic():
            secteur = form.save()
            produits.instance = secteur
            produits.save()
        messages.success(request, f"Secteur {secteur.nom} enregistré.")
        return redirect("secteur_modifier", pk=secteur.pk) if "continuer" in request.POST else redirect("secteurs")
    return _page(request, "gestion/secteur.html", "secteurs", form=form, produits=produits,
                 titre=f"Secteur {secteur.nom}" if secteur.pk else "Ajouter un secteur")


# ---------------------------------------------------------------- dépenses et ventes d'une fiche

@admin_requis
def finances(request, pk):
    fiche = get_object_or_404(Fiche.objects.select_related("producteur"), pk=pk)
    # Les lignes vides sont datées du début de la semaine ; une ligne laissée telle quelle est ignorée.
    initial = [{"date": fiche.semaine}] * DepensesFormSet.extra
    depenses = DepensesFormSet(request.POST or None, instance=fiche, prefix="depenses", initial=initial)
    ventes = VentesFormSet(request.POST or None, instance=fiche, prefix="ventes", initial=initial)
    if request.method == "POST" and depenses.is_valid() and ventes.is_valid():
        with transaction.atomic():
            depenses.save()
            ventes.save()
        messages.success(request, f"Dépenses et ventes de {fiche.producteur.nom} enregistrées.")
        return redirect(f"{reverse('fiche_producteur', args=[fiche.producteur_id])}?semaine={fiche.semaine}")
    return _page(request, "gestion/finances.html", "tableau", fiche=fiche, depenses=depenses, ventes=ventes)


# ---------------------------------------------------------------- prêts

def _f(n):
    return f"{n:,}".replace(",", "\u202f")


@admin_requis
def prets(request):
    if request.method == "POST" and "supprimer" in request.POST:
        pret = get_object_or_404(Pret, pk=request.POST["supprimer"])
        pret.delete()
        messages.success(request, "Opération supprimée.")
        return redirect("prets")
    action = request.POST.get("action")
    form = PretForm(request.POST if action == "accorder" else None,
                    initial={"date": date.today(), "producteur": request.GET.get("producteur")}, prefix="pret")
    rembt = RemboursementForm(request.POST if action == "rembourser" else None,
                              initial={"date": date.today()}, prefix="rembt")
    if action == "accorder" and form.is_valid():
        pret = form.save()
        messages.success(request, f"Prêt de {_f(pret.montant)} F accordé à {pret.producteur.nom} "
                                  f"(à rembourser : {_f(pret.total_du)} F).")
        return redirect("prets")
    if action == "rembourser" and rembt.is_valid():
        r = rembt.save()
        messages.success(request, f"Remboursement de {_f(r.montant)} F enregistré pour {r.producteur.nom} "
                                  f"(reste {_f(r.pret_rembourse.reste)} F).")
        return redirect("prets")
    lignes, tot = portefeuille_prets()
    filtre = request.GET.get("statut")
    if filtre in ("retard", "en_cours", "rembourse"):
        lignes = [l for l in lignes if l["statut"] == filtre]
    remboursements = Pret.objects.filter(type=Pret.TYPE_REMBOURSEMENT).select_related("producteur", "pret_rembourse")[:100]
    return _page(request, "gestion/prets.html", "prets", form=form, rembt=rembt, lignes=lignes, tot=tot,
                 filtre=filtre, remboursements=remboursements)


# ---------------------------------------------------------------- caisse du centre

@admin_requis
def caisse(request):
    if request.method == "POST" and "supprimer" in request.POST:
        op = get_object_or_404(OperationCaisse, pk=request.POST["supprimer"])
        op.delete()
        messages.success(request, "Opération supprimée.")
        return redirect(request.get_full_path())
    form = OperationCaisseForm(request.POST or None, request.FILES or None, initial={"date": date.today()})
    if request.method == "POST" and form.is_valid():
        op = form.save(commit=False)
        op.saisie_par = request.user
        op.save()
        sens = "Entrée" if op.est_entree else "Dépense"
        messages.success(request, f"{sens} de {_f(op.montant)} F enregistrée : {op.libelle}.")
        return redirect(request.get_full_path())
    choix = request.GET.get("periode") or "mois"
    try:
        d, f = date.fromisoformat(request.GET.get("debut", "")), date.fromisoformat(request.GET.get("fin", ""))
    except ValueError:
        d = f = None
    if choix == "libre" and not (d and f):
        choix = "mois"
    debut, fin = rapports.bornes(choix, debut=d, fin=f)
    return _page(request, "gestion/caisse.html", "caisse", form=form, b=bilan_centre(debut, fin),
                 debut=debut, fin=fin, choix=choix, periodes=rapports.PERIODES,
                 titre=rapports.titre_periode(debut, fin), requete=request.GET.urlencode())


@admin_requis
def fiche_supprimer(request, pk):
    fiche = get_object_or_404(Fiche.objects.select_related("producteur"), pk=pk)
    if request.method == "POST":
        nom, semaine = fiche.producteur.nom, fiche.semaine
        fiche.delete()
        messages.success(request, f"La fiche de {nom} (semaine du {semaine:%d/%m/%Y}) a été supprimée.")
        return redirect("fiche_producteur", pk=fiche.producteur_id)
    return _page(request, "gestion/confirmer_suppression.html", "tableau", fiche=fiche,
                 retour=f"{reverse('fiche_producteur', args=[fiche.producteur_id])}?semaine={fiche.semaine}")


@admin_requis
def sauvegarde(request):
    """Fait une copie de sécurité toute fraîche et la télécharge sur l'ordinateur de l'administrateur."""
    from django.http import FileResponse
    from .sauvegarde import faire_sauvegarde
    cible = faire_sauvegarde()
    return FileResponse(open(cible, "rb"), as_attachment=True, filename=cible.name)
