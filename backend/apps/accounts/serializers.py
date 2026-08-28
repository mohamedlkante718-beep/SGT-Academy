from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Role, User, UserRole


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "country", "roles", "date_joined"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "country", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        learner_role, _ = Role.objects.get_or_create(
            name=Role.LEARNER, defaults={"description": "Apprenant"}
        )
        UserRole.objects.get_or_create(user=user, role=learner_role)
        return user
