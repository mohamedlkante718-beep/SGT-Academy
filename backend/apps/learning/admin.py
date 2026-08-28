from django.contrib import admin

from .models import CourseProgress, Enrollment, LessonProgress


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "source", "created_at")
    list_filter = ("source",)
    search_fields = ("user__email", "course__title")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "watched_seconds")
    list_filter = ("status",)


@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "percent_complete", "completed_at")
