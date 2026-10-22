#!/bin/bash
# Installe ou met à jour l'application sur PythonAnywhere, dans une console Bash :
#     bash ~/suivi-producteurs/installer_pythonanywhere.sh
# Par défaut, le site est gageetudes.pythonanywhere.com (le nom du compte). Pour une autre adresse :
#     bash ~/suivi-producteurs/installer_pythonanywhere.sh www.mon-domaine.org
set -e

DOMAINE="${1:-$USER.pythonanywhere.com}"
DOSSIER="$(cd "$(dirname "$0")" && pwd)"
VENV="$HOME/.virtualenvs/suivi"
WSGI="${WSGI_DIR:-/var/www}/$(echo "$DOMAINE" | tr '.' '_' | tr 'A-Z' 'a-z')_wsgi.py"
cd "$DOSSIER"

echo "== 1/6 Environnement Python (quelques minutes la première fois)"
[ -d "$VENV" ] || python3.13 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r requirements.txt
PY="$VENV/bin/python"

echo "== 2/6 Clé secrète"
[ -f .cle_secrete ] || "$PY" -c "import secrets; print(secrets.token_urlsafe(50))" > .cle_secrete
chmod 600 .cle_secrete
export DJANGO_DEBUG=0 DJANGO_ALLOWED_HOSTS="$DOMAINE" DJANGO_SECRET_KEY="$(cat .cle_secrete)"

echo "== 3/6 Base de données"
"$PY" manage.py migrate --noinput

echo "== 4/6 Fiches Excel d'octobre (aucun doublon si on relance)"
"$PY" manage.py charger_fiches_excel

echo "== 5/6 Fichiers de style et images"
"$PY" manage.py collectstatic --noinput -v0

echo "== 6/6 Fichier de démarrage du site : $WSGI"
if [ -f "$WSGI" ] && ! grep -q "suivi-producteurs" "$WSGI"; then
    cp "$WSGI" "$WSGI.sauvegarde-$(date +%Y%m%d-%H%M%S)"
    echo "   L'ancien fichier a été sauvegardé à côté (.sauvegarde-…)."
fi
cat > "$WSGI" <<WSGIEOF
# Suivi des producteurs CIAF — généré par installer_pythonanywhere.sh
import os
import sys

CHEMIN = "$DOSSIER"
if CHEMIN not in sys.path:
    sys.path.insert(0, CHEMIN)
os.environ["DJANGO_SETTINGS_MODULE"] = "suivi.settings"
os.environ["DJANGO_DEBUG"] = "0"
os.environ["DJANGO_ALLOWED_HOSTS"] = "$DOMAINE"
with open(os.path.join(CHEMIN, ".cle_secrete")) as f:
    os.environ["DJANGO_SECRET_KEY"] = f.read().strip()

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
WSGIEOF

if "$PY" manage.py shell -v0 -c "from django.contrib.auth.models import User; import sys; sys.exit(0 if User.objects.filter(is_superuser=True).exists() else 1)"; then
    echo "== Le compte administrateur existe déjà."
else
    echo
    echo "== Création du compte ADMINISTRATEUR (le vôtre). Choisissez un nom (ex. chef) et un mot de passe."
    echo "   (Le mot de passe ne s'affiche pas pendant la frappe : c'est normal.)"
    if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then "$PY" manage.py createsuperuser --noinput --email ""
    else "$PY" manage.py createsuperuser --email ""; fi
fi

cat <<FIN

============================================================
 Installation terminée. Il reste 4 réglages dans l'onglet « Web »
 de PythonAnywhere, pour le site $DOMAINE :

  • Virtualenv          : $VENV
  • Source code         : $DOSSIER
  • Static files        : URL  /static/
                          Directory  $DOSSIER/staticfiles
  • Force HTTPS         : Enabled

 Puis cliquez sur le gros bouton vert « Reload ».
 Ouvrez ensuite : https://$DOMAINE/gestion/
============================================================
FIN
