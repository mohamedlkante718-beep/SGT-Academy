from .base import *  # noqa
from decouple import Csv, config

DEBUG = config("DEBUG", default=False, cast=bool)

# L'API est appelée depuis plusieurs origines (site public, app mobile web,
# éventuels futurs domaines) et n'utilise que des tokens JWT en en-tête
# (jamais de cookie de session) : élargir CORS à toutes origines n'expose pas
# de session. À restreindre à une liste explicite si des cookies apparaissent.
CORS_ALLOW_ALL_ORIGINS = True

# CSRF_TRUSTED_ORIGINS : détecté automatiquement sur Railway (variable fournie
# par la plateforme), sinon à renseigner explicitement (ex: PythonAnywhere).
_railway_domain = config("RAILWAY_PUBLIC_DOMAIN", default="")
_csrf_trusted = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
if _csrf_trusted:
    CSRF_TRUSTED_ORIGINS = _csrf_trusted
elif _railway_domain:
    CSRF_TRUSTED_ORIGINS = [f"https://{_railway_domain}"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Nécessaire derrière le proxy HTTPS de Railway
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Le stockage S3 n'est activé que si un bucket et des identifiants sont
# réellement fournis : sinon, boto3 plante à la moindre écriture de fichier
# (ex: image de couverture d'une formation) avec une config vide. Tant que
# S3 n'est pas branché, on retombe sur le stockage disque par défaut de
# Django (non persistant entre redéploiements, mais fonctionnel).
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")

if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID:
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    _aws_endpoint_url = config("AWS_S3_ENDPOINT_URL", default="")  # ex: R2/B2
    if _aws_endpoint_url:
        AWS_S3_ENDPOINT_URL = _aws_endpoint_url
    _aws_region = config("AWS_S3_REGION_NAME", default="")
    if _aws_region:
        AWS_S3_REGION_NAME = _aws_region
    AWS_QUERYSTRING_EXPIRE = 300  # URL signées à courte expiration (§15)

# Email : activé seulement si des identifiants SMTP sont fournis (ex: Gmail +
# mot de passe d'application) — sinon on garde le backend "console" (aucun
# envoi réel), même logique que pour S3 : ne jamais planter faute de config.
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
    EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=f"SGT Academy <{EMAIL_HOST_USER}>")
    # Sans timeout, une connexion SMTP bloquée (réseau, pare-feu) fait attendre
    # indéfiniment toute la requête HTTP jusqu'au SIGKILL du worker gunicorn —
    # ce qui plante la page en entier (ex: validation d'un paiement) au lieu
    # d'échouer proprement et d'être rattrapé par le try/except de l'envoi.
    EMAIL_TIMEOUT = 10
