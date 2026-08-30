from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course


class Company(TimeStampedModel):
    name = models.CharField(max_length=200, verbose_name="nom")
    email = models.EmailField(verbose_name="email")
    phone = models.CharField(max_length=32, blank=True, verbose_name="téléphone")
    contact_name = models.CharField(max_length=200, blank=True, verbose_name="nom du contact")
    country = models.CharField(max_length=2, default="ML", verbose_name="pays")

    class Meta:
        verbose_name = "entreprise"
        verbose_name_plural = "entreprises"

    def __str__(self):
        return self.name


class CompanyUser(TimeStampedModel):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"
    ROLE_CHOICES = [(ADMIN, "Administrateur entreprise"), (EMPLOYEE, "Employé")]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="members", verbose_name="entreprise")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_memberships",
        verbose_name="utilisateur",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=EMPLOYEE, verbose_name="rôle")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "user"], name="unique_company_user"),
        ]
        verbose_name = "employé d'entreprise"
        verbose_name_plural = "employés d'entreprise"

    def __str__(self):
        return f"{self.user} @ {self.company} ({self.role})"


class CompanyLicense(TimeStampedModel):
    """Lot de licences achetées par une entreprise pour une formation donnée (§21)."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="licenses", verbose_name="entreprise")
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="company_licenses", verbose_name="formation"
    )
    total_seats = models.PositiveIntegerField(verbose_name="places totales")
    used_seats = models.PositiveIntegerField(default=0, verbose_name="places utilisées")
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name="acheté le")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="expire le")

    class Meta:
        verbose_name = "licence entreprise"
        verbose_name_plural = "licences entreprise"

    def __str__(self):
        return f"{self.company} — {self.course} ({self.used_seats}/{self.total_seats})"
