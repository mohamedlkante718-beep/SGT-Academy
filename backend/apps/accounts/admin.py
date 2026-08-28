from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Permission, Profile, Role, User, UserRole


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    ordering = ("-date_joined",)
    list_display = ("email", "first_name", "last_name", "country", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "country")
    search_fields = ("email", "first_name", "last_name", "phone")
    inlines = [ProfileInline, UserRoleInline]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "phone", "country")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )
    readonly_fields = ("date_joined",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "description")
    search_fields = ("codename",)
