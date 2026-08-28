from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Certificate, CertificateVerification
from .serializers import CertificateSerializer


class MyCertificatesView(generics.ListAPIView):
    """GET /api/v1/certificates/ — certificats de l'apprenant connecté (§19)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CertificateSerializer

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user).order_by("-issued_at")


class CertificateDetailView(generics.RetrieveAPIView):
    """GET /api/v1/certificates/{id}/ — détail d'un certificat (propriétaire uniquement)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CertificateSerializer

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)


class CertificateVerifyView(APIView):
    """
    GET /api/v1/certificates/verify/{code}/ — vérification publique (§19).
    Sans authentification, mais limitée en débit pour éviter le scraping/l'énumération.
    Chaque consultation est journalisée (CertificateVerification), y compris les échecs.
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verify"

    def get(self, request, code):
        certificate = Certificate.objects.filter(code=code, is_revoked=False).first()
        is_valid = certificate is not None

        CertificateVerification.objects.create(
            certificate=certificate,
            code_checked=code,
            ip_address=request.META.get("REMOTE_ADDR"),
            was_valid=is_valid,
        )

        if not is_valid:
            return Response({"valid": False, "code": code})

        return Response(
            {
                "valid": True,
                "code": certificate.code,
                "learner_name": certificate.learner_name_snapshot,
                "course_title": certificate.course_title_snapshot,
                "issued_at": certificate.issued_at,
            }
        )
