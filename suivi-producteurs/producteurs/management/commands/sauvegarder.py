"""Copie de sécurité de la base de données (fiches, prêts, caisse…) et des fichiers envoyés (logo, reçus).

    python manage.py sauvegarder              → ~/sauvegardes-suivi/suivi-AAAA-MM-JJ-HHMMSS.zip
    python manage.py sauvegarder --garder 30  → garde les 30 dernières copies

L'application fait déjà une copie par jour toute seule ; cette commande sert avant une mise à jour."""

from django.core.management.base import BaseCommand

from producteurs.sauvegarde import dossier_sauvegardes, faire_sauvegarde


class Command(BaseCommand):
    help = "Fait une copie de sécurité de la base de données et des fichiers envoyés."

    def add_arguments(self, parser):
        parser.add_argument("--dossier", default=None)
        parser.add_argument("--garder", type=int, default=30, help="nombre de copies à conserver")

    def handle(self, dossier, garder, **options):
        cible = faire_sauvegarde(dossier or dossier_sauvegardes(), garder)
        if cible is None:
            self.stdout.write("Pas encore de base de données : rien à sauvegarder.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Sauvegarde faite : {cible}"))
