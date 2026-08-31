import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def create_enrollment_on_paid(sender, instance: Payment, **kwargs):
    """
    Débloque l'accès à la formation UNIQUEMENT quand le statut passe à PAID
    (jamais depuis une information cliente — §11/§14).
    """
    if instance.status != Payment.PAID:
        return
    ensure_enrollment_and_notify(instance)


def ensure_enrollment_and_notify(payment: Payment):
    """
    Crée l'inscription (si absente) pour un paiement PAID et prévient
    l'apprenant par email. Appelée à la fois par le signal post_save (pour
    tout futur déclencheur automatique, ex: webhook d'un prestataire) et
    explicitement par l'admin (validation manuelle) — pour ne jamais dépendre
    uniquement du signal.
    """
    from apps.learning.models import Enrollment

    enrollment, created = Enrollment.objects.get_or_create(
        user=payment.user,
        course=payment.course,
        defaults={"source": Enrollment.PURCHASE},
    )

    if created:
        _send_payment_confirmation_email(payment)

    return enrollment, created


def _send_payment_confirmation_email(payment: Payment):
    """
    Prévient l'apprenant que son paiement est validé, avec un lien direct vers
    l'application. N'envoie rien si aucun identifiant email n'est configuré
    (backend "console" par défaut) et ne doit jamais faire échouer la
    validation du paiement si l'envoi rate.
    """
    app_url = settings.MOBILE_APP_URL or "#"
    first_name = payment.user.first_name or ""
    try:
        send_mail(
            subject="Votre paiement est validé — accédez à votre formation",
            message=(
                f"Bonjour {first_name},\n\n"
                f"Votre paiement pour la formation « {payment.course.title} » a été validé.\n"
                f"Connectez-vous dès maintenant pour commencer : {app_url}\n\n"
                f"À bientôt,\nL'équipe SGT Academy"
            ),
            from_email=None,
            recipient_list=[payment.user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Échec de l'envoi de l'email de confirmation de paiement (référence=%s)", payment.reference
        )
