from django.contrib import admin

from .models import Company, CompanyLicense, CompanyUser


class CompanyUserInline(admin.TabularInline):
    model = CompanyUser
    extra = 0


class CompanyLicenseInline(admin.TabularInline):
    model = CompanyLicense
    extra = 0


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "country")
    inlines = [CompanyUserInline, CompanyLicenseInline]
