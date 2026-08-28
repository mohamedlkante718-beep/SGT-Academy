from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course
from apps.payments.models import Payment


class Coupon(TimeStampedModel):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    DISCOUNT_TYPE_CHOICES = [(PERCENT, "Pourcentage"), (FIXED, "Montant fixe")]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default=PERCENT)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="XOF", blank=True)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Vide = illimité")
    used_count = models.PositiveIntegerField(default=0)

    courses = models.ManyToManyField(Course, blank=True, related_name="coupons", help_text="Vide = toutes les formations")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class CouponUsage(TimeStampedModel):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="usages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coupon_usages")
    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name="coupon_usages")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["coupon", "user"], name="unique_coupon_usage_per_user"),
        ]

    def __str__(self):
        return f"{self.coupon} — {self.user}"
