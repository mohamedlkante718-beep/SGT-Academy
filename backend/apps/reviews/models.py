from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course


class Review(TimeStampedModel):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    STATUS_CHOICES = [(PENDING, "En attente"), (APPROVED, "Approuvé"), (REJECTED, "Rejeté")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_review_per_user_course"),
            models.CheckConstraint(check=models.Q(rating__gte=1) & models.Q(rating__lte=5), name="rating_between_1_and_5"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.course} ({self.rating}★)"
