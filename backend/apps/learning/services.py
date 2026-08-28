from django.utils import timezone

from apps.courses.models import Lesson

from .models import CourseProgress, LessonProgress


def recompute_course_progress(user, course):
    """Recalcule la progression agrégée d'une formation après complétion d'une leçon (§14)."""
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = LessonProgress.objects.filter(
        user=user, lesson__module__course=course, status=LessonProgress.COMPLETED
    ).count()

    percent = int((completed_lessons / total_lessons) * 100) if total_lessons else 0

    progress, _ = CourseProgress.objects.get_or_create(user=user, course=course)
    progress.percent_complete = percent
    if percent >= 100 and not progress.completed_at:
        progress.completed_at = timezone.now()
    progress.save(update_fields=["percent_complete", "completed_at", "updated_at"])
    return progress


def mark_lesson_complete(user, lesson):
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    progress.status = LessonProgress.COMPLETED
    progress.completed_at = timezone.now()
    progress.save(update_fields=["status", "completed_at", "updated_at"])

    course = lesson.module.course
    course_progress = recompute_course_progress(user, course)
    course_progress.last_lesson = lesson
    course_progress.save(update_fields=["last_lesson", "updated_at"])
    return progress
