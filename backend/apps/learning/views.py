from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, Lesson, Module

from .models import Enrollment, LessonProgress
from .permissions import user_has_access_to_course, user_has_access_to_lesson
from .serializers import ModuleProgressOutlineSerializer, MyCourseSerializer
from .services import mark_lesson_complete


class MyCoursesView(generics.ListAPIView):
    """GET /api/v1/my-courses/ — formations de l'apprenant connecté, avec progression (§13)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MyCourseSerializer

    def get_queryset(self):
        return (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course")
            .order_by("-created_at")
        )


class CourseProgressView(APIView):
    """GET /api/v1/courses/{slug}/progress — programme + statut de chaque leçon (§14)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug, status=Course.PUBLISHED)
        if not user_has_access_to_course(request.user, course):
            raise PermissionDenied("Vous n'avez pas accès à cette formation.")

        progress_entries = LessonProgress.objects.filter(
            user=request.user, lesson__module__course=course
        )
        progress_map = {entry.lesson_id: entry for entry in progress_entries}

        modules = Module.objects.filter(course=course).prefetch_related("lessons").order_by("order")
        serializer = ModuleProgressOutlineSerializer(
            modules, many=True, context={"progress_map": progress_map}
        )
        return Response(serializer.data)


class LessonCompleteView(APIView):
    """POST /api/v1/lessons/{id}/complete — marque une leçon terminée (§14/§16)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        if not user_has_access_to_lesson(request.user, lesson):
            raise PermissionDenied("Vous n'avez pas accès à cette leçon.")

        mark_lesson_complete(request.user, lesson)
        return Response({"lesson_id": str(lesson.id), "status": LessonProgress.COMPLETED})
