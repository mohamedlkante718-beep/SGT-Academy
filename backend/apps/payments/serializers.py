from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.coupons.models import Coupon, CouponUsage

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "reference", "course_slug", "course_title", "amount", "currency",
            "method", "status", "manual_reference_submitted", "created_at", "validated_at",
        ]
        read_only_fields = fields


class PurchaseSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES, default=Payment.MANUAL)
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate_coupon_code(self, value):
        if not value:
            return value
        try:
            coupon = Coupon.objects.get(code__iexact=value, is_active=True)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Coupon invalide.")

        now = timezone.now()
        if coupon.start_date and now < coupon.start_date:
            raise serializers.ValidationError("Ce coupon n'est pas encore actif.")
        if coupon.end_date and now > coupon.end_date:
            raise serializers.ValidationError("Ce coupon a expiré.")
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            raise serializers.ValidationError("Ce coupon a atteint son nombre maximal d'utilisations.")
        return value

    def apply_coupon(self, course, amount: Decimal, user):
        code = self.validated_data.get("coupon_code")
        if not code:
            return amount, None

        coupon = Coupon.objects.get(code__iexact=code, is_active=True)
        if coupon.courses.exists() and not coupon.courses.filter(pk=course.pk).exists():
            raise serializers.ValidationError({"coupon_code": "Ce coupon ne s'applique pas à cette formation."})
        if CouponUsage.objects.filter(coupon=coupon, user=user).exists():
            raise serializers.ValidationError({"coupon_code": "Vous avez déjà utilisé ce coupon."})

        if coupon.discount_type == Coupon.PERCENT:
            discount = amount * (coupon.discount_value / Decimal("100"))
        else:
            discount = coupon.discount_value

        new_amount = max(amount - discount, Decimal("0"))
        return new_amount, coupon


class ManualProofSerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=200)
    proof = serializers.FileField(required=False)

    ALLOWED_CONTENT_TYPES = ["image/png", "image/jpeg", "application/pdf"]
    MAX_SIZE_BYTES = 5 * 1024 * 1024

    def validate_proof(self, value):
        if value.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError("Format non autorisé (PNG, JPEG ou PDF uniquement).")
        if value.size > self.MAX_SIZE_BYTES:
            raise serializers.ValidationError("Fichier trop volumineux (5 Mo maximum).")
        return value
