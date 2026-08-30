import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Base commune : identifiant UUID (non énumérable) + horodatage."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="identifiant")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="modifié le")

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(TimeStampedModel):
    """Suppression logique : l'enregistrement reste en base mais est masqué par défaut."""

    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="supprimé le")

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class AuditLog(TimeStampedModel):
    """Traçabilité des actions sensibles (§33) : validation paiement manuel, changement de rôle, etc."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        verbose_name="auteur",
    )
    action = models.CharField(max_length=100, verbose_name="action")
    target_type = models.CharField(max_length=100, blank=True, verbose_name="type de cible")
    target_id = models.CharField(max_length=64, blank=True, verbose_name="identifiant de la cible")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="métadonnées")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="adresse IP")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]
        verbose_name = "journal d'audit"
        verbose_name_plural = "journaux d'audit"

    def __str__(self):
        return f"{self.action} — {self.target_type}:{self.target_id}"


class Setting(models.Model):
    """Paramètres éditables sans toucher au code (§50) : logo, slogan, textes, etc."""

    key = models.CharField(max_length=100, unique=True, verbose_name="clé")
    value = models.JSONField(default=dict, blank=True, verbose_name="valeur")
    description = models.CharField(max_length=255, blank=True, verbose_name="description")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="modifié le")

    class Meta:
        verbose_name = "paramètre"
        verbose_name_plural = "paramètres"

    def __str__(self):
        return self.key
