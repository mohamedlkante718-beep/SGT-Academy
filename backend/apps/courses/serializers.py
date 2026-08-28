from rest_framework import serializers

from .models import Category, Course, Instructor, Lesson, Module


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon"]


class InstructorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Instructor
        fields = ["id", "full_name", "headline", "is_verified"]


class CourseListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructors = InstructorSerializer(many=True, read_only=True)
    modules_count = serializers.IntegerField(source="modules.count", read_only=True)
    students_count = serializers.IntegerField(source="enrollments.count", read_only=True)

    class Meta:
        model = Course
        fields = [
            "slug", "title", "short_description", "cover_image",
            "level", "duration_hours", "price", "promo_price", "currency",
            "certificate_available", "categories", "instructors",
            "modules_count", "students_count",
        ]


# Une leçon n'expose jamais sa clé de stockage vidéo (§15) : uniquement
# les métadonnées nécessaires à l'affichage du programme (§9/§16).
class LessonOutlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "order", "duration_seconds", "is_preview"]


class ModuleOutlineSerializer(serializers.ModelSerializer):
    lessons = LessonOutlineSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "title", "description", "order", "lessons"]


class CourseDetailSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    instructors = InstructorSerializer(many=True, read_only=True)
    modules = ModuleOutlineSerializer(many=True, read_only=True)
    students_count = serializers.IntegerField(source="enrollments.count", read_only=True)

    class Meta:
        model = Course
        fields = [
            "slug", "title", "short_description", "description",
            "objectives", "skills_acquired", "prerequisites",
            "cover_image", "level", "duration_hours",
            "price", "promo_price", "currency", "certificate_available",
            "categories", "instructors", "modules", "students_count",
            "seo_title", "seo_description",
        ]
