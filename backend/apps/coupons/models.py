from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course
from apps.payments.models import Payment


class Coupon(TimeStampedModel):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    DISCOUNT_TYPE_CHOICES = [(PERCENT, "Pourcentage"), (FIXED, "Montant fixe")]

    code = models.CharField(max_length=50, unique=True, verbose_name="code")
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, default=PERCENT, verbose_name="type de réduction"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valeur de la réduction")
    currency = models.CharField(max_length=3, default="XOF", blank=True, verbose_name="devise")

    start_date = models.DateTimeField(null=True, blank=True, verbose_name="date de début")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="date de fin")
    max_uses = models.PositiveIntegerField(
        null=True, blank=True, help_text="Vide = illimité", verbose_name="utilisations maximum"
    )
    used_count = models.PositiveIntegerField(default=0, verbose_name="nombre d'utilisations")

    courses = models.ManyToManyField(
        Course,
        blank=True,
        related_name="coupons",
        help_text="Vide = toutes les formations",
        verbose_name="formations",
    )
    is_active = models.BooleanField(default=True, verbose_name="actif")

    class Meta:
        verbose_name = "coupon"
        verbose_name_plural = "coupons"

    def __str__(self):
        return self.code


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages", verbose_name="coupon")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_usages", verbose_name="utilisateur"
    )
    payment = models.ForeignKey(
        Payment,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="coupon_usages",
        verbose_name="paiement",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["coupon", "user"], name="unique_coupon_usage_per_user"),
        ]
        verbose_name = "utilisation de coupon"
        verbose_name_plural = "utilisations de coupon"

    def __str__(self):
        return f"{self.coupon} — {self.user}"
