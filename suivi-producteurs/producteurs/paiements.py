"""Paiement mensuel des producteurs.

1. Le comptable choisit les producteurs payés ce mois-ci et les montants, puis envoie au promoteur.
2. Le promoteur valide, ou refuse avec un commentaire (le comptable corrige et renvoie).
3. Une fois l'argent remis, le comptable marque le mois « payé » : chaque paiement devient une sortie
   de la caisse du centre (rubrique « Paiement des producteurs »)."""

import calendar
from datetime import date, timedelta

from django import forms
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .caisse import portefeuille_prets
from .gestion import admin_requis
from .models import (MODES_PAIEMENT, CategorieCaisse, Fiche, LignePaiement, OperationCaisse, PaiementMensuel,
                     Producteur, peut_preparer_paiements, peut_valider_paiements)
from .services import MOIS_NOMS


def nom_mois(m):
    return f"{MOIS_NOMS[m.month - 1].capitalize()} {m.year}"


def _mois_ou_404(texte):
    from django.http import Http404
    try:
        a, m = (int(x) for x in texte.split("-"))
        return date(a, m, 1)
    except (ValueError, TypeError):
        raise Http404("Mois invalide")


def _droits(request):
    return {"peut_preparer": peut_preparer_paiements(request.user), "peut_valider": peut_valider_paiements(request.user)}


def _page(request, gabarit, **ctx):
    return render(request, gabarit, {"est_admin": True, "onglet": "paiements", **_droits(request), **ctx})


class PayerForm(forms.Form):
    date_paiement = forms.DateField(label="Date du paiement", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    mode_paiement = forms.ChoiceField(label="Mode de paiement", choices=MODES_PAIEMENT)


@admin_requis
def paiements(request):
    """Liste des mois, et choix d'un mois à préparer."""
    aujourd_hui = date.today()
    mois_choix = []
    m = aujourd_hui.replace(day=1)
    for _ in range(14):  # ce mois-ci et les 13 précédents
        mois_choix.append({"valeur": f"{m:%Y-%m}", "nom": nom_mois(m)})
        m = (m.replace(day=1) - timedelta(days=1)).replace(day=1)
    if request.method == "POST" and peut_preparer_paiements(request.user):
        return redirect("paiement_mois", mois=request.POST.get("mois") or f"{aujourd_hui:%Y-%m}")
    liste = PaiementMensuel.objects.prefetch_related("lignes").select_related("prepare_par", "valide_par")
    return _page(request, "gestion/paiements.html", paiements=liste, mois_choix=mois_choix)


def _infos_du_mois(mois):
    """Pour aider le comptable : valeur déclarée à la fin du mois, ventes du mois et reste des prêts."""
    fin = mois.replace(day=calendar.monthrange(mois.year, mois.month)[1])
    infos = {}
    fiches = (Fiche.objects.filter(semaine__gte=mois, semaine__lte=fin)
              .prefetch_related("valeurs", "ventes").order_by("semaine"))
    for f in fiches:
        i = infos.setdefault(f.producteur_id, {"valeur": None, "ventes": 0, "fiches": 0})
        i["valeur"] = f.total_valeurs
        i["ventes"] += f.total_ventes
        i["fiches"] += 1
    lignes, _ = portefeuille_prets(jusqu_au=fin)
    for l in lignes:
        i = infos.setdefault(l["pret"].producteur_id, {"valeur": None, "ventes": 0, "fiches": 0})
        i["reste_pret"] = i.get("reste_pret", 0) + l["reste"]
    return infos


def _entier(texte):
    texte = (texte or "").replace(" ", "").replace(" ", "").replace("\xa0", "").strip()
    if not texte:
        return None
    if not texte.isdigit():
        raise ValueError
    return int(texte)


@admin_requis
def paiement_mois(request, mois):
    mois = _mois_ou_404(mois)
    paiement = PaiementMensuel.objects.filter(mois=mois).first()
    droits = _droits(request)
    action = request.POST.get("action") if request.method == "POST" else None

    # ---- le promoteur valide ou refuse
    if action in ("valider", "refuser"):
        if not (paiement and droits["peut_valider"] and paiement.statut == PaiementMensuel.A_VALIDER):
            messages.error(request, "Seul le promoteur peut valider un paiement envoyé pour validation.")
            return redirect("paiement_mois", mois=f"{mois:%Y-%m}")
        commentaire = request.POST.get("commentaire", "").strip()
        if action == "refuser" and not commentaire:
            messages.error(request, "Expliquez au comptable ce qu'il faut revoir avant de refuser.")
            return redirect("paiement_mois", mois=f"{mois:%Y-%m}")
        paiement.statut = PaiementMensuel.VALIDE if action == "valider" else PaiementMensuel.REFUSE
        paiement.valide_par, paiement.valide_le, paiement.commentaire = request.user, timezone.now(), commentaire
        paiement.save()
        messages.success(request, f"{paiement} : " + ("validé. Le comptable peut payer." if action == "valider"
                                                      else "refusé et renvoyé au comptable."))
        return redirect("paiement_mois", mois=f"{mois:%Y-%m}")

    # ---- le comptable marque le mois payé : sorties de caisse
    payer = PayerForm(request.POST if action == "payer" else None,
                      initial={"date_paiement": date.today(), "mode_paiement": "especes"})
    if action == "payer":
        if not (paiement and droits["peut_preparer"] and paiement.statut == PaiementMensuel.VALIDE):
            messages.error(request, "Ce paiement n'est pas encore validé par le promoteur.")
            return redirect("paiement_mois", mois=f"{mois:%Y-%m}")
        if payer.is_valid():
            categorie, _ = CategorieCaisse.objects.get_or_create(nom="Paiement des producteurs",
                                                                 sens=CategorieCaisse.SORTIE)
            with transaction.atomic():
                for l in paiement.lignes.select_related("producteur"):
                    l.operation = OperationCaisse.objects.create(
                        date=payer.cleaned_data["date_paiement"], categorie=categorie,
                        libelle=f"Paiement de {nom_mois(mois).lower()}" + (f" — {l.motif}" if l.motif else ""),
                        montant=l.montant, mode_paiement=payer.cleaned_data["mode_paiement"],
                        tiers=l.producteur.nom, saisie_par=request.user)
                    l.save()
                paiement.statut, paiement.paye_par = PaiementMensuel.PAYE, request.user
                paiement.date_paiement = payer.cleaned_data["date_paiement"]
                paiement.mode_paiement = payer.cleaned_data["mode_paiement"]
                paiement.save()
            messages.success(request, f"{paiement} : marqué payé. Les sorties sont dans la caisse du centre.")
            return redirect("paiement_mois", mois=f"{mois:%Y-%m}")

    # ---- le comptable supprime un brouillon
    if action == "supprimer":
        if paiement and droits["peut_preparer"] and paiement.modifiable:
            paiement.delete()
            messages.success(request, f"Paiement de {nom_mois(mois).lower()} supprimé.")
        return redirect("paiements")

    # ---- le comptable choisit les producteurs et les montants
    modifiable = droits["peut_preparer"] and (paiement is None or paiement.modifiable)
    producteurs = list(Producteur.objects.filter(actif=True).select_related("responsable"))
    if paiement:
        existantes = {l.producteur_id: l for l in paiement.lignes.all()}
        # Un producteur désactivé mais déjà dans le paiement reste affiché.
        producteurs += [l.producteur for l in paiement.lignes.select_related("producteur")
                        if l.producteur_id not in {p.pk for p in producteurs}]
    else:
        # Nouveau mois : on propose les producteurs et montants du dernier paiement.
        dernier = PaiementMensuel.objects.filter(mois__lt=mois).first()
        existantes = {l.producteur_id: l for l in dernier.lignes.all()} if dernier else {}
    infos = _infos_du_mois(mois)
    lignes, erreurs = [], 0
    for p in producteurs:
        l = existantes.get(p.pk)
        ligne = {"producteur": p, "coche": l is not None, "montant": l.montant if l else None,
                 "motif": l.motif if l else "", "info": infos.get(p.pk, {}), "erreur": None,
                 "montant_brut": None}
        if action in ("enregistrer", "envoyer") and modifiable:
            ligne["coche"] = request.POST.get(f"p_{p.pk}") == "1"
            ligne["montant_brut"] = request.POST.get(f"m_{p.pk}", "")
            ligne["motif"] = request.POST.get(f"o_{p.pk}", "").strip()[:150]
            try:
                ligne["montant"] = _entier(ligne["montant_brut"])
            except ValueError:
                ligne["erreur"] = "Nombre entier uniquement"
            if ligne["coche"] and not ligne["erreur"] and not ligne["montant"]:
                ligne["erreur"] = "Indiquez le montant"
            erreurs += bool(ligne["coche"] and ligne["erreur"])
        lignes.append(ligne)

    if action in ("enregistrer", "envoyer"):
        if not modifiable:
            messages.error(request, "Ce paiement ne peut plus être modifié.")
            return redirect("paiement_mois", mois=f"{mois:%Y-%m}")
        choisies = [l for l in lignes if l["coche"]]
        if erreurs:
            messages.error(request, "Certains montants sont manquants ou incorrects. Corrigez les cases en rouge.")
        elif action == "envoyer" and not choisies:
            messages.error(request, "Cochez au moins un producteur avant d'envoyer au promoteur.")
        else:
            with transaction.atomic():
                if paiement is None:
                    paiement = PaiementMensuel(mois=mois)
                paiement.prepare_par = request.user
                if action == "envoyer":
                    paiement.statut, paiement.envoye_le = PaiementMensuel.A_VALIDER, timezone.now()
                paiement.save()
                paiement.lignes.all().delete()
                LignePaiement.objects.bulk_create([
                    LignePaiement(paiement=paiement, producteur=l["producteur"], montant=l["montant"], motif=l["motif"])
                    for l in choisies])
            total = sum(l["montant"] for l in choisies)
            messages.success(request, f"{paiement} : {len(choisies)} producteur{'s' if len(choisies) > 1 else ''}, "
                                      f"{total:,} F".replace(",", " ")
                                      + (" — envoyé au promoteur pour validation." if action == "envoyer"
                                         else " — enregistré (pas encore envoyé)."))
            return redirect("paiement_mois", mois=f"{mois:%Y-%m}")

    if not modifiable:
        lignes = [l for l in lignes if l["coche"]] if paiement else []
    return _page(request, "gestion/paiement_mois.html", paiement=paiement, mois=mois, titre=nom_mois(mois),
                 lignes=lignes, modifiable=modifiable, payer=payer,
                 total=sum(l["montant"] or 0 for l in lignes if l["coche"]),
                 nb=sum(1 for l in lignes if l["coche"]), repris=paiement is None and bool(existantes))


@admin_requis
def paiement_imprimer(request, mois):
    paiement = get_object_or_404(PaiementMensuel.objects.select_related("prepare_par", "valide_par", "paye_par"),
                                 mois=_mois_ou_404(mois))
    return render(request, "gestion/paiement_imprimable.html", {
        "paiement": paiement, "titre": nom_mois(paiement.mois),
        "lignes": paiement.lignes.select_related("producteur"), "genere_le": timezone.localtime(),
        "retour": reverse("paiement_mois", args=[f"{paiement.mois:%Y-%m}"]),
    })


def paiements_en_attente(user):
    """Nombre de paiements qui attendent une action de cet utilisateur (pour le menu)."""
    statuts = []
    if peut_valider_paiements(user):
        statuts.append(PaiementMensuel.A_VALIDER)
    if peut_preparer_paiements(user):
        statuts += [PaiementMensuel.VALIDE, PaiementMensuel.REFUSE]
    return PaiementMensuel.objects.filter(statut__in=statuts).count() if statuts else 0
