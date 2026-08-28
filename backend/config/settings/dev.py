from .base import *  # noqa
from decouple import config

DEBUG = config("DEBUG", default=True, cast=bool)

if not ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CORS_ALLOW_ALL_ORIGINS = True
