from rest_framework import serializers

from apps.courses.models import Lesson, Module

from .models import CourseProgress, Enrollment, LessonProgress


class MyCourseSerializer(serializers.ModelSerializer):
    course_slug = serializers.CharField(source="course.slug", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    cover_image = serializers.ImageField(source="course.cover_image", read_only=True)
    percent_complete = serializers.SerializerMethodField()
    last_lesson_id = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ["course_slug", "course_title", "cover_image", "percent_complete", "last_lesson_id", "created_at"]

    def get_progress(self, obj):
        return CourseProgress.objects.filter(user=obj.user, course=obj.course).first()

    def get_percent_complete(self, obj):
        progress = self.get_progress(obj)
        return progress.percent_complete if progress else 0

    def get_last_lesson_id(self, obj):
        progress = self.get_progress(obj)
        return progress.last_lesson_id if progress and progress.last_lesson_id else None


class LessonProgressOutlineSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "order", "duration_seconds", "is_preview", "status"]

    def get_status(self, lesson):
        progress_map = self.context.get("progress_map", {})
        entry = progress_map.get(lesson.id)
        return entry.status if entry else "NOT_STARTED"


class ModuleProgressOutlineSerializer(serializers.ModelSerializer):
    lessons = LessonProgressOutlineSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "title", "order", "lessons"]
