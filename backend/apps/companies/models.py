from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    contact_name = models.CharField(max_length=200, blank=True)
    country = models.CharField(max_length=2, default="ML")

    def __str__(self):
        return self.name


class CompanyUser(TimeStampedModel):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"
    ROLE_CHOICES = [(ADMIN, "Administrateur entreprise"), (EMPLOYEE, "Employé")]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=EMPLOYEE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "user"], name="unique_company_user"),
        ]

    def __str__(self):
        return f"{self.user} @ {self.company} ({self.role})"


class CompanyLicense(TimeStampedModel):
    """Lot de licences achetées par une entreprise pour une formation donnée (§21)."""

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="licenses")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="company_licenses")
    total_seats = models.PositiveIntegerField()
    used_seats = models.PositiveIntegerField(default=0)
    purchased_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.company} — {self.course} ({self.used_seats}/{self.total_seats})"
