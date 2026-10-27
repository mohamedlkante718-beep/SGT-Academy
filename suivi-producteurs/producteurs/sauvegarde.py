"""Copies de sécurité de la base de données et des fichiers envoyés (logo, reçus).

Le compte gratuit de PythonAnywhere n'a pas de tâches programmées : l'application fait donc elle-même
une copie par jour, à la première visite de la journée, et l'administrateur peut en télécharger une."""

import sqlite3
import time
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings


def dossier_sauvegardes():
    return Path(settings.SAUVEGARDES_DIR)


def faire_sauvegarde(dossier=None, garder=30):
    """Crée suivi-AAAA-MM-JJ-HHMMSS.zip (base + fichiers envoyés) et garde les `garder` dernières copies."""
    base = Path(settings.DATABASES["default"]["NAME"])
    if not base.exists():
        return None
    dossier = Path(dossier or dossier_sauvegardes())
    dossier.mkdir(parents=True, exist_ok=True)
    dossier.chmod(0o700)
    cible = dossier / f"suivi-{datetime.now():%Y-%m-%d-%H%M%S}.zip"
    # Copie cohérente même si quelqu'un enregistre une fiche au même moment. Elle est faite dans le
    # dossier des sauvegardes (pas dans /tmp), et les connexions sont bien fermées avant de zipper.
    copie = dossier / f".copie-{cible.stem}.sqlite3"
    src, dst = sqlite3.connect(base), sqlite3.connect(copie)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    try:
        with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(copie, "db.sqlite3")
            media = Path(settings.MEDIA_ROOT)
            if media.exists():
                for f in media.rglob("*"):
                    if f.is_file():
                        z.write(f, Path("media") / f.relative_to(media))
    finally:
        copie.unlink(missing_ok=True)
    cible.chmod(0o600)
    anciennes = sorted(dossier.glob("suivi-*.zip"))[:-garder] if garder > 0 else []
    for f in anciennes:
        f.unlink()
    return cible


def derniere_sauvegarde():
    copies = sorted(dossier_sauvegardes().glob("suivi-*.zip"))
    return copies[-1] if copies else None


class SauvegardeQuotidienne:
    """Une fois par jour au plus, à la première visite, fait une copie de sécurité.
    On ne regarde le dossier qu'une fois par heure, pour ne pas ralentir le site."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.prochain_controle = 0

    def __call__(self, request):
        reponse = self.get_response(request)
        if settings.SAUVEGARDE_AUTO and time.time() >= self.prochain_controle:
            self.prochain_controle = time.time() + 3600
            try:
                derniere = derniere_sauvegarde()
                if derniere is None or time.time() - derniere.stat().st_mtime > 23 * 3600:
                    faire_sauvegarde()
            except Exception:  # une copie ratée ne doit jamais empêcher d'utiliser le site
                pass
        return reponse
