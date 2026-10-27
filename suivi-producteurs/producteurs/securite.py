"""Protection contre le piratage : blocage des essais répétés de code PIN, en-têtes de sécurité,
session courte pour l'administrateur."""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import TentativeConnexion


def adresse_ip(request):
    """Adresse du visiteur. Chez PythonAnywhere, elle est transmise dans l'en-tête X-Real-IP."""
    ip = request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or ""
    return ip.strip() or None


def est_bloque(identifiant, ip):
    """Trop d'essais ratés récemment, pour ce numéro ou depuis cette adresse ?"""
    depuis = timezone.now() - timedelta(minutes=settings.CONNEXION_BLOCAGE_MINUTES)
    rates = TentativeConnexion.objects.filter(quand__gte=depuis, reussie=False)
    if identifiant and rates.filter(identifiant=identifiant).count() >= settings.CONNEXION_ESSAIS_MAX:
        return True
    return bool(ip) and rates.filter(ip=ip).count() >= settings.CONNEXION_ESSAIS_MAX_IP


def noter(identifiant, ip, reussie):
    TentativeConnexion.objects.create(identifiant=(identifiant or "")[:150], ip=ip, reussie=reussie)
    if reussie:
        # Une connexion réussie remet le compteur à zéro pour ce numéro.
        TentativeConnexion.objects.filter(identifiant=identifiant, reussie=False).delete()
    # Le journal garde 6 mois.
    TentativeConnexion.objects.filter(quand__lt=timezone.now() - timedelta(days=180)).delete()


class EnTetesSecurite:
    """Ajoute la politique de sécurité du contenu (CSP) : le navigateur refuse tout script ou
    contenu venant d'un autre site, et la page ne peut pas être affichée dans un cadre d'un autre site."""

    CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
           "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; "
           "img-src 'self' data: blob:; connect-src 'self'; worker-src 'self'; manifest-src 'self'; "
           "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reponse = self.get_response(request)
        reponse.setdefault("Content-Security-Policy", self.CSP)
        reponse.setdefault("Permissions-Policy", "camera=(self), microphone=(), geolocation=()")
        return reponse


class SessionAdministrateur:
    """Les comptes administrateur sont déconnectés après quelques heures sans activité (les producteurs
    restent connectés sur leur téléphone). Ainsi un ordinateur oublié ouvert ne reste pas accessible."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff:
            request.session.set_expiry(settings.SESSION_ADMIN_SECONDES)
        return self.get_response(request)
