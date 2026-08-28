from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from .filters import CourseFilter
from .models import Course
from .serializers import CourseDetailSerializer, CourseListSerializer


class PublishedCourseQuerysetMixin:
    def get_base_queryset(self):
        return (
            Course.objects.filter(status=Course.PUBLISHED)
            .prefetch_related("categories", "instructors__user", "modules__lessons")
        )


class CourseListView(PublishedCourseQuerysetMixin, generics.ListAPIView):
    """GET /api/v1/courses/ — catalogue public (§8)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CourseListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ["title", "short_description"]
    ordering_fields = ["price", "duration_hours", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.get_base_queryset()


class CourseDetailView(PublishedCourseQuerysetMixin, generics.RetrieveAPIView):
    """GET /api/v1/courses/{slug}/ — détail d'une formation (§9)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CourseDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return self.get_base_queryset()
