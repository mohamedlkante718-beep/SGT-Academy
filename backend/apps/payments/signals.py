from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment


@receiver(post_save, sender=Payment)
def create_enrollment_on_paid(sender, instance: Payment, **kwargs):
    """
    Débloque l'accès à la formation UNIQUEMENT quand le statut passe à PAID
    (jamais depuis une information cliente — §11/§14).
    """
    if instance.status != Payment.PAID:
        return

    from apps.learning.models import Enrollment

    Enrollment.objects.get_or_create(
        user=instance.user,
        course=instance.course,
        defaults={"source": Enrollment.PURCHASE},
    )
