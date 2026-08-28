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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="certificates")

    code = models.CharField(max_length=64, unique=True, help_text="Ex: SGT-2026-QGIS-000125")
    learner_name_snapshot = models.CharField(max_length=300)
    course_title_snapshot = models.CharField(max_length=200)
    instructor_name_snapshot = models.CharField(max_length=300, blank=True)
    duration_hours_snapshot = models.PositiveIntegerField(default=0)

    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_storage_key = models.CharField(max_length=500, blank=True)
    qr_code_storage_key = models.CharField(max_length=500, blank=True)
    is_revoked = models.BooleanField(default=False)

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
        Certificate, null=True, blank=True, on_delete=models.SET_NULL, related_name="verifications"
    )
    code_checked = models.CharField(max_length=64)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    was_valid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "vérification de certificat"
        verbose_name_plural = "vérifications de certificat"

    def __str__(self):
        return f"{self.code_checked} — {'valide' if self.was_valid else 'invalide'}"
