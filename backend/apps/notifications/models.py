from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class Notification(TimeStampedModel):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    CHANNEL_CHOICES = [(IN_APP, "In-app"), (EMAIL, "Email"), (SMS, "SMS")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default=IN_APP)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user} — {self.title}"
