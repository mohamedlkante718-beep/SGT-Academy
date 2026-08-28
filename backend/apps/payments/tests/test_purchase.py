from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.coupons.models import Coupon
from apps.courses.models import Course
from apps.learning.models import Enrollment

from ..models import Payment


class PurchaseTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="learner@example.com", password="Sup3rSecret!", first_name="Learn", last_name="Er"
        )
        self.course = Course.objects.create(
            title="QGIS pour débutants", price=Decimal("25000"), currency="XOF", status=Course.PUBLISHED
        )
        self.url = reverse("payments:purchase", args=[self.course.slug])

    def test_purchase_requires_authentication(self):
        response = self.client.post(self.url, {"method": Payment.MANUAL}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purchase_creates_pending_manual_payment(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"method": Payment.MANUAL}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["status"], Payment.PENDING)
        self.assertEqual(Decimal(response.data["amount"]), Decimal("25000"))
        # Un paiement en attente ne doit jamais débloquer l'accès :
        self.assertFalse(Enrollment.objects.filter(user=self.user, course=self.course).exists())

    def test_mobile_money_is_explicitly_refused_without_provider(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"method": Payment.MOBILE_MONEY}, format="json")
        self.assertEqual(response.status_code, status.HTTP_501_NOT_IMPLEMENTED)

    def test_purchase_is_idempotent_while_pending(self):
        self.client.force_authenticate(user=self.user)
        first = self.client.post(self.url, {"method": Payment.MANUAL}, format="json")
        second = self.client.post(self.url, {"method": Payment.MANUAL}, format="json")
        self.assertEqual(first.data["reference"], second.data["reference"])
        self.assertEqual(Payment.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_paying_manually_validated_payment_unlocks_course(self):
        """Le passage à PAID (simulant la validation admin) doit créer l'inscription."""
        payment = Payment.objects.create(
            user=self.user, course=self.course, amount=25000, currency="XOF", method=Payment.MANUAL
        )
        self.assertFalse(Enrollment.objects.filter(user=self.user, course=self.course).exists())

        payment.status = Payment.PAID
        payment.save()

        self.assertTrue(Enrollment.objects.filter(user=self.user, course=self.course).exists())

    def test_cannot_purchase_already_enrolled_course(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"method": Payment.MANUAL}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CouponTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="coupon@example.com", password="Sup3rSecret!", first_name="Cou", last_name="Pon"
        )
        self.course = Course.objects.create(
            title="Formation avec coupon", price=Decimal("10000"), currency="XOF", status=Course.PUBLISHED
        )
        self.url = reverse("payments:purchase", args=[self.course.slug])
        self.client.force_authenticate(user=self.user)

    def test_percent_coupon_reduces_amount(self):
        Coupon.objects.create(code="SGT10", discount_type=Coupon.PERCENT, discount_value=10)
        response = self.client.post(
            self.url, {"method": Payment.MANUAL, "coupon_code": "SGT10"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(Decimal(response.data["amount"]), Decimal("9000"))

    def test_invalid_coupon_code_rejected(self):
        response = self.client.post(
            self.url, {"method": Payment.MANUAL, "coupon_code": "DOESNOTEXIST"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ManualProofTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="proof@example.com", password="Sup3rSecret!", first_name="Pro", last_name="Of"
        )
        self.course = Course.objects.create(
            title="Formation preuve", price=Decimal("5000"), currency="XOF", status=Course.PUBLISHED
        )
        self.payment = Payment.objects.create(
            user=self.user, course=self.course, amount=5000, currency="XOF", method=Payment.MANUAL
        )
        self.client.force_authenticate(user=self.user)

    def test_submit_reference_without_file(self):
        url = reverse("payments:manual-proof", args=[self.payment.reference])
        response = self.client.patch(url, {"reference": "OM-2026-000123"}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["manual_reference_submitted"], "OM-2026-000123")
