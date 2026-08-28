#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django est introuvable. Avez-vous activé votre environnement virtuel "
            "et installé requirements.txt ?"
        ) from exc
    execute_from_command_line(sys.argv)
