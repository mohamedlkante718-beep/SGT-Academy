"""
Configuration commune à tous les environnements.
Aucun secret ne doit être écrit en dur ici : tout passe par des variables
d'environnement (voir .env.example à la racine de backend/).
"""

from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tiers
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "django_filters",
    # Applications SGT Academy
    "apps.common",
    "apps.accounts",
    "apps.courses",
    "apps.learning",
    "apps.assessments",
    "apps.payments",
    "apps.coupons",
    "apps.certificates",
    "apps.companies",
    "apps.notifications",
    "apps.reviews",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de données ---
# En production/Railway : DATABASE_URL fourni par le service PostgreSQL.
# En local sans PostgreSQL installé : repli automatique sur SQLite (dev only).
_database_url = config("DATABASE_URL", default="") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DATABASES = {"default": dj_database_url.parse(_database_url, conn_max_age=600)}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation : Français au lancement, Anglais préparé (§37) ---
LANGUAGE_CODE = "fr"
LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
]
TIME_ZONE = config("TIME_ZONE", default="Africa/Bamako")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"  # développement uniquement : la prod utilise le stockage objet (voir storages.py)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/minute",
        "user": "300/minute",
        "login": "10/minute",
        "verify": "30/minute",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SGT Academy API",
    "DESCRIPTION": "API de la plateforme e-learning Safe Green Tech (SGT Academy).",
    "VERSION": "0.1.0",
}

CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())

# --- Site public (pour construire l'URL complète encodée dans le QR code des certificats) ---
PUBLIC_SITE_URL = config("PUBLIC_SITE_URL", default="")

# --- Multi-pays / multi-devises (§36) ---
DEFAULT_CURRENCY = config("DEFAULT_CURRENCY", default="XOF")
SUPPORTED_CURRENCIES = ["XOF", "XAF", "EUR", "USD"]

# --- Celery (tâches asynchrones : emails, PDF certificats, vérif. paiements) ---
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# --- Upload : contrôle des fichiers (§33) ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
