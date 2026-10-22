"""Charge les fiches reprises des fichiers Excel du CIAF (dossier producteurs/donnees/).

Usage : python manage.py charger_fiches_excel
Semaines disponibles : du 1er au 7, du 8 au 14 et du 14 au 20 octobre 2026.
Chaque producteur reçoit les produits de ses fiches. Il est créé sans téléphone ni code PIN :
l'administrateur les complète ensuite (Producteurs → ouvrir un producteur → Téléphone + Code PIN).
Une fiche déjà présente n'est jamais écrasée : on peut relancer la commande sans risque.
"""

import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from producteurs.models import Depense, Fiche, LigneEffectif, LigneValeur, Producteur, Produit, Secteur, Vente
from producteurs.services import cle

DOSSIER = Path(__file__).resolve().parents[2] / "donnees"


class Command(BaseCommand):
    help = "Charge les fiches reprises des fichiers Excel du CIAF (sans écraser une fiche existante)."

    @transaction.atomic
    def handle(self, *args, **options):
        elevage, _ = Secteur.objects.get_or_create(nom="Élevage", defaults={"ordre": 1})
        catalogue = {cle(p.nom): p for p in Produit.objects.filter(secteur=elevage)}
        ordre_noms = []
        for fichier in sorted(DOSSIER.glob("semaine_*.json")):
            donnees = json.loads(fichier.read_text(encoding="utf-8"))
            semaine = date.fromisoformat(donnees["semaine"])
            crees = 0
            for p in donnees["producteurs"]:
                if p["nom"] not in ordre_noms:
                    ordre_noms.append(p["nom"])
                producteur = Producteur.objects.filter(nom=p["nom"]).first()
                if producteur is None:
                    # Numéro provisoire unique, à remplacer par le vrai numéro dans l'administration.
                    rang = ordre_noms.index(p["nom"]) + 1
                    producteur = Producteur.objects.create(nom=p["nom"], telephone=f"A-COMPLETER-{rang:02d}", ordre=rang)
                if Fiche.objects.filter(producteur=producteur, semaine=semaine).exists():
                    continue
                fiche = Fiche.objects.create(producteur=producteur, semaine=semaine, observations=p["observations"],
                                             statut=Fiche.VALIDEE, commentaire="Reprise du fichier Excel CIAF.")
                for modele, lignes in ((LigneEffectif, p["effectifs"]), (LigneValeur, p["valeurs"])):
                    for l in lignes:
                        produit = catalogue.get(cle(l["libelle"]))
                        if produit is None:
                            # Produit apparu dans l'Excel mais absent du catalogue : on l'ajoute à l'Élevage.
                            compter_seulement = l["libelle"].startswith(("Œufs", "Mortalités", "Nouvelles éclosions"))
                            produit = Produit.objects.create(secteur=elevage, nom=l["libelle"],
                                                             unite="œufs" if l["libelle"].startswith("Œufs") else "têtes",
                                                             valoriser=not compter_seulement, ordre=100 + len(catalogue))
                            catalogue[cle(produit.nom)] = produit
                        modele.objects.create(fiche=fiche, produit=produit, **l)
                        producteur.produits.add(produit)
                for d in p.get("depenses", []):
                    Depense.objects.create(fiche=fiche, **d)
                for v in p.get("ventes", []):
                    Vente.objects.create(fiche=fiche, **v)
                crees += 1
            self.stdout.write(self.style.SUCCESS(f"Semaine du {semaine:%d/%m/%Y} : {crees} fiche(s) créée(s)."))
