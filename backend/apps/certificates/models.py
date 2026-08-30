from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course


class Certificate(TimeStampedModel):
    """
    Certificat professionnel. Le numéro (`code`) est unique et sert de clé
    de vérification publique sur /verify/{code} (§19).
    Les champs "snapshot" figent les informations au moment de l'émission
    (le nom de la formation ou du formateur ne doivent pas changer rétroactivement
    sur un certificat déjà délivré).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates", verbose_name="utilisateur"
    )
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="certificates", verbose_name="formation")

    code = models.CharField(
        max_length=64, unique=True, help_text="Ex: SGT-2026-QGIS-000125", verbose_name="code"
    )
    learner_name_snapshot = models.CharField(max_length=300, verbose_name="nom de l'apprenant (figé)")
    course_title_snapshot = models.CharField(max_length=200, verbose_name="titre de la formation (figé)")
    instructor_name_snapshot = models.CharField(max_length=300, blank=True, verbose_name="nom du formateur (figé)")
    duration_hours_snapshot = models.PositiveIntegerField(default=0, verbose_name="durée en heures (figée)")

    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="délivré le")
    pdf_storage_key = models.CharField(max_length=500, blank=True, verbose_name="clé de stockage du PDF")
    qr_code_storage_key = models.CharField(max_length=500, blank=True, verbose_name="clé de stockage du QR code")
    is_revoked = models.BooleanField(default=False, verbose_name="révoqué")

    class Meta:
        indexes = [models.Index(fields=["code"])]
        ordering = ["-issued_at"]
        verbose_name = "certificat"
        verbose_name_plural = "certificats"

    def __str__(self):
        return self.code


class CertificateVerification(TimeStampedModel):
    """Journal des consultations de la page publique de vérification (anti-abus, §19)."""

    certificate = models.ForeignKey(
        Certificate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verifications",
        verbose_name="certificat",
    )
    code_checked = models.CharField(max_length=64, verbose_name="code vérifié")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="adresse IP")
    was_valid = models.BooleanField(default=False, verbose_name="était valide")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "vérification de certificat"
        verbose_name_plural = "vérifications de certificat"

    def __str__(self):
        return f"{self.code_checked} — {'valide' if self.was_valid else 'invalide'}"
