from django.contrib import admin

from .models import Certificate, CertificateVerification


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("code", "user", "course", "issued_at", "is_revoked")
    list_filter = ("is_revoked",)
    search_fields = ("code", "user__email", "course_title_snapshot")


@admin.register(CertificateVerification)
class CertificateVerificationAdmin(admin.ModelAdmin):
    list_display = ("code_checked", "was_valid", "ip_address", "created_at")
    readonly_fields = [f.name for f in CertificateVerification._meta.fields]

    def has_add_permission(self, request):
        return False
