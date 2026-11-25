import io
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.core import management
from django.http import HttpResponse

# Vue temporaire : permet de télécharger une sauvegarde JSON des données réelles
# (hors tables techniques) directement depuis le navigateur, sans passer par la
# console Railway (peu fiable pour taper des commandes) ni par un accès direct
# à la base Postgres (non joignable depuis l'extérieur). À retirer une fois la
# migration d'hébergement terminée.
EXCLUDED_APPS = [
    "contenttypes",
    "auth.permission",
    "sessions",
    "admin.logentry",
    "token_blacklist",
]


@staff_member_required
def export_backup(request):
    buffer = io.StringIO()
    management.call_command(
        "dumpdata",
        exclude=EXCLUDED_APPS,
        natural_foreign=True,
        natural_primary=True,
        indent=2,
        stdout=buffer,
    )
    filename = f"sgt_academy_backup_{datetime.now():%Y%m%d_%H%M%S}.json"
    response = HttpResponse(buffer.getvalue(), content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
