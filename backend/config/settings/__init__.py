import os

env = os.environ.get("DJANGO_ENV", "dev")

if env == "prod":
    from .prod import *  # noqa
else:
    from .dev import *  # noqa
