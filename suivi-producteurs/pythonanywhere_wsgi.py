# Modèle de fichier WSGI pour PythonAnywhere.
# À copier dans l'onglet « Web » → lien « WSGI configuration file », en remplaçant tout son contenu.
import os
import sys

CHEMIN = "/home/gageetudes/SGT-Academy/suivi-producteurs"  # dossier qui contient manage.py
if CHEMIN not in sys.path:
    sys.path.insert(0, CHEMIN)

os.environ["DJANGO_SETTINGS_MODULE"] = "suivi.settings"
os.environ["DJANGO_DEBUG"] = "0"
os.environ["DJANGO_ALLOWED_HOSTS"] = "suivi.gage-etudes.org"
os.environ["DJANGO_SECRET_KEY"] = "REMPLACEZ-PAR-UNE-LONGUE-CHAINE-ALEATOIRE"

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
