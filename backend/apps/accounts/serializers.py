from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from .models import Role, User, UserRole


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone", "country",
            "roles", "date_joined", "email_verified",
        ]
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


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        # On retrouve d'abord LE compte par son email, puis on compare le code
        # uniquement sur cette fiche précise : le code d'un compte ne peut
        # donc jamais valider le compte d'un autre, même s'il le connaît.
        try:
            user = User.objects.get(email__iexact=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Aucun compte avec cet email."})

        if user.email_verified:
            raise serializers.ValidationError("Cet email est déjà vérifié.")

        if not user.email_verification_code or not user.email_verification_expires_at:
            raise serializers.ValidationError("Aucun code en attente — demandez un nouvel envoi.")

        if timezone.now() > user.email_verification_expires_at:
            raise serializers.ValidationError("Ce code a expiré — demandez un nouvel envoi.")

        if attrs["code"] != user.email_verification_code:
            raise serializers.ValidationError({"code": "Code incorrect."})

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.email_verified = True
        user.email_verification_code = None
        user.email_verification_expires_at = None
        user.save(update_fields=["email_verified", "email_verification_code", "email_verification_expires_at"])
        return user


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self._user = User.objects.get(email__iexact=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Aucun compte avec cet email.")
        if self._user.email_verified:
            raise serializers.ValidationError("Cet email est déjà vérifié.")
        return value

    def save(self):
        return self._user
