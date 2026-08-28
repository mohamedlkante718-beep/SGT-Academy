from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.courses.models import Course

from ..models import Certificate, CertificateVerification
from ..services import issue_certificate


class CertificateVerificationTests(APITestCase):
    def setUp(self):
        self.course = Course.objects.create(title="Formation Vérif", price=1000, status=Course.PUBLISHED)
        self.user = User.objects.create_user(
            email="cert@example.com", password="Sup3rSecret!", first_name="Cer", last_name="Tif"
        )
        self.certificate = issue_certificate(self.user, self.course)

    def test_verify_valid_code_is_public_and_returns_details(self):
        url = reverse("certificates:certificate-verify", args=[self.certificate.code])
        response = self.client.get(url)  # pas d'authentification
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["learner_name"], self.user.get_full_name())
        self.assertTrue(
            CertificateVerification.objects.filter(certificate=self.certificate, was_valid=True).exists()
        )

    def test_verify_unknown_code_returns_invalid_without_error(self):
        url = reverse("certificates:certificate-verify", args=["SGT-2026-FAKE-000001"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["valid"])
        self.assertTrue(
            CertificateVerification.objects.filter(code_checked="SGT-2026-FAKE-000001", was_valid=False).exists()
        )

    def test_revoked_certificate_is_reported_invalid(self):
        self.certificate.is_revoked = True
        self.certificate.save(update_fields=["is_revoked"])
        url = reverse("certificates:certificate-verify", args=[self.certificate.code])
        response = self.client.get(url)
        self.assertFalse(response.data["valid"])

    def test_issue_certificate_is_idempotent(self):
        second = issue_certificate(self.user, self.course)
        self.assertEqual(second.id, self.certificate.id)
        self.assertEqual(Certificate.objects.filter(user=self.user, course=self.course).count(), 1)

    def test_other_user_cannot_see_someone_elses_certificate(self):
        stranger = User.objects.create_user(
            email="stranger2@example.com", password="Sup3rSecret!", first_name="Str", last_name="Anger"
        )
        self.client.force_authenticate(user=stranger)
        response = self.client.get(
            reverse("certificates:certificate-detail", args=[self.certificate.id])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
