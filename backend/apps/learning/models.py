from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course, Lesson


class Enrollment(TimeStampedModel):
    """
    Preuve d'accès à une formation. Ne doit être créée que par le backend,
    après confirmation d'un paiement (statut PAID) ou attribution d'une
    licence entreprise — jamais depuis une information envoyée par le client.
    """

    PURCHASE = "PURCHASE"
    COMPANY_LICENSE = "COMPANY_LICENSE"
    COUPON_FREE = "COUPON_FREE"
    SOURCE_CHOICES = [
        (PURCHASE, "Achat individuel"),
        (COMPANY_LICENSE, "Licence entreprise"),
        (COUPON_FREE, "Accès gratuit via coupon"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=PURCHASE)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_enrollment_per_user_course"),
        ]

    def __str__(self):
        return f"{self.user} → {self.course}"


class LessonProgress(TimeStampedModel):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    STATUS_CHOICES = [(STARTED, "Commencé"), (COMPLETED, "Terminé")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_entries")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STARTED)
    watched_seconds = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "lesson"], name="unique_lesson_progress_per_user"),
        ]

    def __str__(self):
        return f"{self.user} — {self.lesson} ({self.status})"


class CourseProgress(TimeStampedModel):
    """Progression agrégée par formation, mise à jour à chaque LessonProgress terminée."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_progress")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="progress_entries")
    percent_complete = models.PositiveSmallIntegerField(default=0)
    last_lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "course"], name="unique_course_progress_per_user"),
        ]

    def __str__(self):
        return f"{self.user} — {self.course} ({self.percent_complete}%)"
