from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .emails import send_verification_code_email
from .serializers import (
    RegisterSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register — création de compte apprenant (§10)."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = user.generate_email_verification_code()
        send_verification_code_email(user, code)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    """POST /api/v1/auth/verify-email/ — valide le code reçu par email."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verify"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data)


class ResendVerificationView(APIView):
    """POST /api/v1/auth/resend-verification/ — renvoie un nouveau code."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        code = user.generate_email_verification_code()
        send_verification_code_email(user, code)
        return Response({"detail": "Un nouveau code a été envoyé."})


class EmailVerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Refuse la connexion tant que l'email n'est pas vérifié — le blocage se
    fait après l'authentification classique (email + mot de passe corrects)
    pour ne jamais révéler si un email existe à quelqu'un qui ne connaît
    pas déjà le mot de passe.
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.email_verified:
            raise ValidationError(
                "Adresse email non vérifiée. Vérifiez votre boîte mail ou redemandez un code."
            )
        return data


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login — connexion par email/mot de passe (§10), limitée en débit."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"
    serializer_class = EmailVerifiedTokenObtainPairSerializer


class LogoutView(APIView):
    """POST /api/v1/auth/logout — invalide le refresh token (blacklist)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise ValidationError({"refresh": "Ce champ est requis."})
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError as exc:
            raise ValidationError({"refresh": str(exc)})
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveAPIView):
    """GET /api/v1/auth/me — profil de l'utilisateur connecté."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
