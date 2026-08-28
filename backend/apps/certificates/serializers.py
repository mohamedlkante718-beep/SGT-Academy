from rest_framework import serializers

from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    course_slug = serializers.CharField(source="course.slug", read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "code", "course_slug", "course_title_snapshot",
            "learner_name_snapshot", "instructor_name_snapshot",
            "duration_hours_snapshot", "issued_at", "is_revoked",
        ]
        read_only_fields = fields


class CertificateVerificationResultSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    code = serializers.CharField()
    learner_name = serializers.CharField(required=False)
    course_title = serializers.CharField(required=False)
    issued_at = serializers.DateTimeField(required=False)
