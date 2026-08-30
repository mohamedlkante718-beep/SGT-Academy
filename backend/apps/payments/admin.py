from django.contrib import admin
from django.utils import timezone

from .models import Payment, PaymentTransaction


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ("provider", "provider_transaction_id", "status", "raw_response", "created_at")
    can_delete = False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "user", "course", "amount", "currency", "method", "status",
        "manual_reference_submitted", "created_at",
    )
    list_filter = ("status", "method", "currency")
    search_fields = ("reference", "user__email", "manual_reference_submitted")
    inlines = [PaymentTransactionInline]
    actions = ["validate_manual_payment"]
    readonly_fields = ("diagnostic_inscription",)

    @admin.display(description="Diagnostic : inscription créée ?")
    def diagnostic_inscription(self, obj):
        if not obj.pk:
            return "—"
        from apps.learning.models import Enrollment

        enrollment = Enrollment.objects.filter(user=obj.user, course=obj.course).first()
        if enrollment:
            return f"OUI — créée le {enrollment.created_at:%d/%m/%Y %H:%M} (source : {enrollment.source})"
        return "NON — aucune inscription trouvée pour cet utilisateur et cette formation."

    @admin.action(description="Valider le(s) paiement(s) manuel(s) sélectionné(s) → PAID")
    def validate_manual_payment(self, request, queryset):
        updated = 0
        for payment in queryset.filter(method=Payment.MANUAL, status=Payment.PENDING):
            payment.status = Payment.PAID
            payment.validated_by = request.user
            payment.validated_at = timezone.now()
            payment.save(update_fields=["status", "validated_by", "validated_at"])
            updated += 1
        self.message_user(request, f"{updated} paiement(s) validé(s).")
