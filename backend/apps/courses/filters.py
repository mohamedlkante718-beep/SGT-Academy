import django_filters

from .models import Course


class CourseFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="categories__slug", lookup_expr="exact")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Course
        fields = ["category", "level", "certificate_available", "min_price", "max_price"]
