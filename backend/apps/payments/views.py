from decimal import Decimal

from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.coupons.models import CouponUsage
from apps.courses.models import Course

from .models import Payment
from .serializers import ManualProofSerializer, PaymentSerializer, PurchaseSerializer


class PurchaseView(APIView):
    """
    POST /api/v1/courses/{slug}/purchase — démarre l'achat d'une formation.

    §11/§12 : seul le paiement manuel est réellement opérationnel tant qu'aucun
    prestataire (Mobile Money/carte) n'est contractualisé et configuré. Une
    demande via 'mobile_money' ou 'card' est refusée explicitement plutôt que
    simulée — voir §53 : ne jamais faire semblant qu'un paiement fonctionne.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug, status=Course.PUBLISHED)

        if course.enrollments.filter(user=request.user).exists():
            raise ValidationError("Vous avez déjà accès à cette formation.")

        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data["method"]

        if method != Payment.MANUAL:
            return Response(
                {
                    "error": (
                        "Cette méthode de paiement nécessite les identifiants du fournisseur "
                        "(Mobile Money / carte) — non configurés pour le moment. "
                        "Utilisez le paiement manuel pour continuer."
                    )
                },
                status=status.HTTP_501_NOT_IMPLEMENTED,
            )

        existing = Payment.objects.filter(
            user=request.user, course=course, status__in=[Payment.PENDING, Payment.PAID]
        ).first()
        if existing:
            return Response(PaymentSerializer(existing).data, status=status.HTTP_200_OK)

        amount = course.promo_price if course.promo_price is not None else course.price
        coupon = None
        if serializer.validated_data.get("coupon_code"):
            amount, coupon = serializer.apply_coupon(course, Decimal(amount), request.user)

        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=amount,
            currency=course.currency,
            method=Payment.MANUAL,
            status=Payment.PENDING,
        )
        if coupon:
            CouponUsage.objects.create(coupon=coupon, user=request.user, payment=payment)
            coupon.used_count = coupon.used_count + 1
            coupon.save(update_fields=["used_count"])

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentStatusView(APIView):
    """GET /api/v1/payments/{reference}/ — statut d'un paiement (propriétaire uniquement)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, reference):
        payment = get_object_or_404(Payment, reference=reference, user=request.user)
        return Response(PaymentSerializer(payment).data)


class SubmitManualProofView(APIView):
    """
    PATCH /api/v1/payments/{reference}/proof/ — l'apprenant saisit sa référence
    de paiement manuel et peut joindre une preuve (§12). Le paiement reste
    PENDING jusqu'à validation par un administrateur.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, reference):
        payment = get_object_or_404(
            Payment, reference=reference, user=request.user, method=Payment.MANUAL
        )
        if payment.status != Payment.PENDING:
            raise ValidationError("Ce paiement n'est plus en attente.")

        serializer = ManualProofSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment.manual_reference_submitted = serializer.validated_data["reference"]
        proof = serializer.validated_data.get("proof")
        if proof:
            storage_key = default_storage.save(f"payment_proofs/{payment.reference}/{proof.name}", proof)
            payment.manual_proof_storage_key = storage_key
        payment.save(update_fields=["manual_reference_submitted", "manual_proof_storage_key", "updated_at"])

        return Response(PaymentSerializer(payment).data)
