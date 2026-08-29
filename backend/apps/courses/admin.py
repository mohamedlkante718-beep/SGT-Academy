from django.contrib import admin

from .models import (
    Category,
    Course,
    CourseCategory,
    Instructor,
    InstructorCourse,
    Lesson,
    LessonResource,
    Module,
)


class LessonResourceInline(admin.TabularInline):
    model = LessonResource
    extra = 0


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "is_verified")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "level", "price", "currency", "certificate_available")
    list_filter = ("status", "level", "certificate_available")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    # deleted_at ne doit jamais être rempli à la main : c'est l'action "Supprimer"
    # de la liste qui s'en charge (SoftDeleteModel.delete()) — un remplissage
    # accidentel via le formulaire cache silencieusement la formation partout.
    exclude = ("deleted_at",)
    inlines = [ModuleInline]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("course", "order", "title")
    list_filter = ("course",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("module", "order", "title", "is_preview", "duration_seconds")
    inlines = [LessonResourceInline]


admin.site.register(CourseCategory)
admin.site.register(InstructorCourse)
