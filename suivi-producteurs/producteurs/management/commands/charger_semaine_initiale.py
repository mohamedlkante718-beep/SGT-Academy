"""Charge les 12 producteurs et leurs fiches de la semaine du 14 au 20 octobre 2026 (fichier Excel CIAF).

Usage : python manage.py charger_semaine_initiale
Chaque producteur reçoit les produits de sa fiche Excel. Il est créé sans téléphone ni code PIN :
l'administrateur les complète ensuite (Producteurs → ouvrir un producteur → Téléphone + Code PIN).
"""

import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from producteurs.models import Fiche, LigneEffectif, LigneValeur, Producteur, Produit
from producteurs.services import cle

FICHIER = Path(__file__).resolve().parents[2] / "donnees" / "semaine_2026-10-14.json"


class Command(BaseCommand):
    help = "Charge les fiches de la semaine du 14 au 20 octobre 2026 (sans écraser une fiche existante)."

    @transaction.atomic
    def handle(self, *args, **options):
        donnees = json.loads(FICHIER.read_text(encoding="utf-8"))
        semaine = date.fromisoformat(donnees["semaine"])
        catalogue = {cle(p.nom): p for p in Produit.objects.filter(secteur__nom="Élevage")}
        crees = 0
        for ordre, p in enumerate(donnees["producteurs"], start=1):
            producteur = Producteur.objects.filter(nom=p["nom"]).first()
            if producteur is None:
                # Numéro provisoire unique, à remplacer par le vrai numéro dans l'administration.
                producteur = Producteur.objects.create(nom=p["nom"], telephone=f"A-COMPLETER-{ordre:02d}", ordre=ordre)
            if Fiche.objects.filter(producteur=producteur, semaine=semaine).exists():
                continue
            fiche = Fiche.objects.create(producteur=producteur, semaine=semaine, observations=p["observations"],
                                         statut=Fiche.VALIDEE, commentaire="Reprise du fichier Excel CIAF.")
            for modele, lignes in ((LigneEffectif, p["effectifs"]), (LigneValeur, p["valeurs"])):
                for l in lignes:
                    produit = catalogue.get(cle(l["libelle"]))
                    modele.objects.create(fiche=fiche, produit=produit, **l)
                    if produit:
                        producteur.produits.add(produit)
            crees += 1
        self.stdout.write(self.style.SUCCESS(f"{crees} fiche(s) créée(s) pour la semaine du {semaine:%d/%m/%Y}."))
