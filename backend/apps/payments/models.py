import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course


def generate_payment_reference():
    return str(uuid.uuid4())


class Payment(TimeStampedModel):
    """
    Un paiement n'est jamais considéré confirmé sur la seule foi du client (§11).
    Le passage à PAID doit résulter soit d'une vérification serveur->prestataire,
    soit d'une validation manuelle par un administrateur (paiement manuel, §12).
    """

    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    STATUS_CHOICES = [
        (PENDING, "En attente"),
        (PAID, "Payé"),
        (FAILED, "Échoué"),
        (CANCELLED, "Annulé"),
        (REFUNDED, "Remboursé"),
    ]

    MOBILE_MONEY = "MOBILE_MONEY"
    CARD = "CARD"
    MANUAL = "MANUAL"
    OTHER = "OTHER"
    METHOD_CHOICES = [
        (MOBILE_MONEY, "Mobile Money"),
        (CARD, "Carte bancaire"),
        (MANUAL, "Paiement manuel"),
        (OTHER, "Autre"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments", verbose_name="utilisateur"
    )
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="payments", verbose_name="formation")

    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="montant")
    currency = models.CharField(max_length=3, default="XOF", verbose_name="devise")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=MANUAL, verbose_name="méthode")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, verbose_name="statut")

    reference = models.CharField(
        max_length=64, unique=True, default=generate_payment_reference, editable=False, verbose_name="référence"
    )
    manual_proof_storage_key = models.CharField(
        max_length=500, blank=True, verbose_name="clé de stockage de la preuve"
    )
    manual_reference_submitted = models.CharField(
        max_length=200, blank=True, verbose_name="référence transaction soumise"
    )

    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments_validated",
        help_text="Admin ayant validé un paiement manuel",
        verbose_name="validé par",
    )
    validated_at = models.DateTimeField(null=True, blank=True, verbose_name="validé le")

    class Meta:
        indexes = [models.Index(fields=["status"]), models.Index(fields=["reference"])]
        ordering = ["-created_at"]
        verbose_name = "paiement"
        verbose_name_plural = "paiements"

    def __str__(self):
        return f"{self.reference} — {self.user} — {self.status}"


class PaymentTransaction(TimeStampedModel):
    """Journal des échanges avec le prestataire de paiement (webhooks, vérifications API)."""

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="transactions", verbose_name="paiement")
    provider = models.CharField(
        max_length=50, blank=True, help_text="Ex: cinetpay, paydunya, kkiapay", verbose_name="prestataire"
    )
    provider_transaction_id = models.CharField(
        max_length=200, blank=True, verbose_name="identifiant de transaction du prestataire"
    )
    status = models.CharField(max_length=20, choices=Payment.STATUS_CHOICES, verbose_name="statut")
    raw_response = models.JSONField(default=dict, blank=True, verbose_name="réponse brute")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "transaction de paiement"
        verbose_name_plural = "transactions de paiement"

    def __str__(self):
        return f"{self.payment.reference} — {self.provider} — {self.status}"
