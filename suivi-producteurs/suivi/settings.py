"""Réglages du suivi des producteurs du CIAF/CE (Centre d'Incubation Agroforestière Champ École).

En production (PythonAnywhere), les valeurs sensibles sont lues dans les
variables d'environnement définies en haut du fichier WSGI :
DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-uniquement-a-changer-en-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1")]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "producteurs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "producteurs.securite.EnTetesSecurite",
    "producteurs.securite.SessionAdministrateur",
    "producteurs.sauvegarde.SauvegardeQuotidienne",
]

ROOT_URLCONF = "suivi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "producteurs.views.organisation",
            ],
        },
    },
]

WSGI_APPLICATION = "suivi.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []  # les producteurs se connectent avec un code PIN à 4-6 chiffres

LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Bamako"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
THOUSAND_SEPARATOR = " "

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Fichiers envoyés depuis l'administration (logo).
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "connexion"
LOGIN_REDIRECT_URL = "accueil"
LOGOUT_REDIRECT_URL = "connexion"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 60  # 60 jours : le producteur reste connecté sur son téléphone

# ---- Sécurité (protection contre le piratage)
# Adresse de l'administration Django : cachée (lue dans le fichier .adresse_admin créé par le script
# d'installation) pour que les robots qui essaient « /admin/ » sur tous les sites ne la trouvent pas.
_fichier_admin = BASE_DIR / ".adresse_admin"
ADMIN_URL = (os.environ.get("DJANGO_ADMIN_URL")
             or (_fichier_admin.read_text().strip() if _fichier_admin.exists() else "")
             or "admin/").strip("/") + "/"

# Après 5 codes faux pour un même numéro (ou 20 depuis un même appareil), connexion bloquée 15 minutes.
CONNEXION_ESSAIS_MAX = 5
CONNEXION_ESSAIS_MAX_IP = 20
CONNEXION_BLOCAGE_MINUTES = 15
SESSION_ADMIN_SECONDES = 60 * 60 * 8  # administrateur : déconnecté après 8 heures sans activité

# Copies de sécurité : une par jour, faite par l'application elle-même (en production seulement).
SAUVEGARDES_DIR = os.environ.get("DJANGO_SAUVEGARDES_DIR", str(Path.home() / "sauvegardes-suivi"))
SAUVEGARDE_AUTO = not DEBUG

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # PythonAnywhere reçoit le HTTPS et transmet la requête en indiquant « X-Forwarded-Proto: https ».
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Le navigateur n'utilisera plus que HTTPS pour ce site pendant un an.
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365

# Nom de la structure, affiché dans l'application, les rapports PDF et les fichiers Excel.
ORGANISATION_SIGLE = "CIAF/CE"
ORGANISATION_NOM = "Centre d'Incubation Agroforestière Champ École"

# Jour où commence la semaine de suivi (0 = lundi … 2 = mercredi).
# La fiche CIAF de référence couvre du mercredi 14 au mardi 20 octobre 2026.
SEMAINE_JOUR_DEBUT = int(os.environ.get("SEMAINE_JOUR_DEBUT", "2"))
