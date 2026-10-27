#!/bin/bash
# Installe ou met à jour l'application sur PythonAnywhere, dans une console Bash.
# Créez d'abord l'application web vide (onglet Web → Add a new web app), puis :
#     bash ~/suivi-producteurs/installer_pythonanywhere.sh suivi.gage-etudes.org
# Le script refuse de remplacer le fichier de démarrage d'un autre site déjà en service.
set -e

DOMAINE="$1"
if [ -z "$DOMAINE" ]; then
    echo "Indiquez l'adresse du site, par exemple :"
    echo "    bash $0 suivi.gage-etudes.org"
    exit 1
fi
DOSSIER="$(cd "$(dirname "$0")" && pwd)"
VENV="$HOME/.virtualenvs/suivi"
WSGI="${WSGI_DIR:-/var/www}/$(echo "$DOMAINE" | tr '.' '_' | tr 'A-Z' 'a-z')_wsgi.py"
cd "$DOSSIER"

# Sécurité : ne jamais écraser le fichier de démarrage d'un site existant (seulement le modèle vide
# créé par PythonAnywhere, ou une installation précédente de cette application).
if [ -f "$WSGI" ] && ! grep -q "suivi-producteurs" "$WSGI" && ! grep -qi "hello.world" "$WSGI" && [ "$FORCER" != "1" ]; then
    echo "ARRÊT : $WSGI appartient déjà à un autre site, que ce script ne doit pas remplacer."
    echo "Vérifiez l'adresse indiquée : il faut celle de la NOUVELLE application web créée pour le suivi."
    exit 1
fi
if [ ! -f "$WSGI" ] && [ -z "$WSGI_DIR" ]; then
    echo "ARRÊT : aucune application web « $DOMAINE » n'existe encore sur ce compte."
    echo "Créez-la d'abord : onglet Web → Add a new web app → $DOMAINE → Manual configuration → Python 3.13."
    exit 1
fi

echo "== 1/6 Environnement Python (quelques minutes la première fois)"
[ -d "$VENV" ] || python3.13 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r requirements.txt
PY="$VENV/bin/python"

echo "== 2/6 Clé secrète"
[ -f .cle_secrete ] || "$PY" -c "import secrets; print(secrets.token_urlsafe(50))" > .cle_secrete
chmod 600 .cle_secrete
export DJANGO_DEBUG=0 DJANGO_ALLOWED_HOSTS="$DOMAINE" DJANGO_SECRET_KEY="$(cat .cle_secrete)"

echo "== 3/6 Base de données (copie de sécurité d'abord)"
# Adresse cachée de l'administration Django, choisie au hasard une seule fois.
[ -f .adresse_admin ] || echo "admin-$("$PY" -c "import secrets; print(secrets.token_hex(4))")/" > .adresse_admin
chmod 600 .adresse_admin
"$PY" manage.py sauvegarder || echo "   (Copie de sécurité impossible cette fois-ci : l'installation continue.)"
"$PY" manage.py migrate --noinput

echo "== 4/6 Fiches Excel d'octobre (seulement à la première installation)"
if "$PY" manage.py shell -v0 -c "from producteurs.models import Producteur; import sys; sys.exit(0 if Producteur.objects.exists() else 1)"; then
    echo "   Déjà chargées : rien à faire (les producteurs renommés ou supprimés ne sont pas recréés)."
else
    "$PY" manage.py charger_fiches_excel
fi

echo "== 5/6 Fichiers de style et images"
"$PY" manage.py collectstatic --noinput -v0

echo "== 6/6 Fichier de démarrage du site : $WSGI"
if [ -f "$WSGI" ]; then
    cp "$WSGI" "$WSGI.sauvegarde-$(date +%Y%m%d-%H%M%S)"
fi
cat > "$WSGI" <<WSGIEOF
# Suivi des producteurs CIAF/CE — généré par installer_pythonanywhere.sh
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

CERTIFICAT=""
case "$DOMAINE" in
    *.pythonanywhere.com) ;;  # certificat HTTPS déjà fourni par PythonAnywhere
    *) CERTIFICAT="  • HTTPS certificate   : Let's Encrypt
" ;;
esac

cat <<FIN

============================================================
 Installation terminée. Il reste quelques réglages dans l'onglet « Web »
 de PythonAnywhere, pour le site $DOMAINE :

  • Virtualenv          : $VENV
  • Source code         : $DOSSIER
  • Static files        : URL  /static/
                          Directory  $DOSSIER/staticfiles
$CERTIFICAT  • Force HTTPS         : Enabled

 Copie de sécurité automatique chaque jour : onglet « Tasks », ajoutez
 une tâche quotidienne (Daily) avec cette commande :
   $PY $DOSSIER/manage.py sauvegarder

 Puis cliquez sur le gros bouton vert « Reload ».
 Ouvrez ensuite : https://$DOMAINE/gestion/
 Adresse secrète de l'administration (logo, catégories, journal des
 connexions) — à ne donner à personne :
   https://$DOMAINE/$(cat .adresse_admin)
 (Elle est aussi dans le menu « Réglages » quand vous êtes connecté.)
============================================================
FIN
