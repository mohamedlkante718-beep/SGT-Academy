from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    CHANNEL_CHOICES = [(IN_APP, "In-app"), (EMAIL, "Email"), (SMS, "SMS")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications", verbose_name="utilisateur"
    )
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default=IN_APP, verbose_name="canal")
    title = models.CharField(max_length=200, verbose_name="titre")
    message = models.TextField(verbose_name="message")
    is_read = models.BooleanField(default=False, verbose_name="lu")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="métadonnées")

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]
        verbose_name = "notification"
        verbose_name_plural = "notifications"

    def __str__(self):
        return f"{self.user} — {self.title}"
