from .base import *  # noqa
from decouple import config

DEBUG = False

_railway_domain = config("RAILWAY_PUBLIC_DOMAIN", default="")
if _railway_domain:
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
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default="")  # ex: R2/B2
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="")
AWS_QUERYSTRING_EXPIRE = 300  # URL signées à courte expiration (§15)
