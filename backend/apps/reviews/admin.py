from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("course", "user", "rating", "status", "created_at")
    list_filter = ("status", "rating")
    actions = ["approve", "reject"]

    @admin.action(description="Approuver les avis sélectionnés")
    def approve(self, request, queryset):
        queryset.update(status=Review.APPROVED)

    @admin.action(description="Rejeter les avis sélectionnés")
    def reject(self, request, queryset):
        queryset.update(status=Review.REJECTED)
