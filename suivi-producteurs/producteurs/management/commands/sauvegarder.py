"""Copie de sécurité de la base de données (fiches, prêts, caisse…) et des fichiers envoyés (logo, reçus).

    python manage.py sauvegarder              → ~/sauvegardes-suivi/suivi-AAAA-MM-JJ-HHMM.zip
    python manage.py sauvegarder --garder 30  → garde les 30 dernières copies

À programmer chaque jour dans PythonAnywhere (onglet « Tasks »)."""

import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fait une copie de sécurité de la base de données et des fichiers envoyés."

    def add_arguments(self, parser):
        parser.add_argument("--dossier", default=str(Path.home() / "sauvegardes-suivi"))
        parser.add_argument("--garder", type=int, default=30, help="nombre de copies à conserver")

    def handle(self, dossier, garder, **options):
        base = Path(settings.DATABASES["default"]["NAME"])
        if not base.exists():
            self.stdout.write("Pas encore de base de données : rien à sauvegarder.")
            return
        dossier = Path(dossier)
        dossier.mkdir(parents=True, exist_ok=True)
        dossier.chmod(0o700)
        cible = dossier / f"suivi-{datetime.now():%Y-%m-%d-%H%M%S}.zip"
        with tempfile.TemporaryDirectory() as tmp:
            copie = Path(tmp) / "db.sqlite3"
            # Copie cohérente même si quelqu'un enregistre une fiche au même moment.
            with sqlite3.connect(base) as src, sqlite3.connect(copie) as dst:
                src.backup(dst)
            with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(copie, "db.sqlite3")
                media = Path(settings.MEDIA_ROOT)
                if media.exists():
                    for f in media.rglob("*"):
                        if f.is_file():
                            z.write(f, Path("media") / f.relative_to(media))
        cible.chmod(0o600)
        anciennes = sorted(dossier.glob("suivi-*.zip"))[:-garder] if garder > 0 else []
        for f in anciennes:
            f.unlink()
        self.stdout.write(self.style.SUCCESS(f"Sauvegarde faite : {cible}"))
