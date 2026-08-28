from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Role, User


class RegisterTests(APITestCase):
    def test_register_creates_user_with_learner_role(self):
        url = reverse("accounts:register")
        payload = {
            "email": "alice@example.com",
            "first_name": "Alice",
            "last_name": "Diarra",
            "phone": "+22370000000",
            "country": "ML",
            "password": "Sup3rSecret!",
            "password_confirm": "Sup3rSecret!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        user = User.objects.get(email="alice@example.com")
        self.assertTrue(user.check_password("Sup3rSecret!"))
        self.assertTrue(user.has_role(Role.LEARNER))

    def test_register_rejects_password_mismatch(self):
        url = reverse("accounts:register")
        payload = {
            "email": "bob@example.com",
            "first_name": "Bob",
            "last_name": "Traore",
            "password": "Sup3rSecret!",
            "password_confirm": "Different!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="bob@example.com").exists())


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="carla@example.com", password="Sup3rSecret!", first_name="Carla", last_name="Kone"
        )

    def test_login_returns_access_and_refresh_tokens(self):
        url = reverse("accounts:login")
        response = self.client.post(url, {"email": "carla@example.com", "password": "Sup3rSecret!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_fails_with_wrong_password(self):
        url = reverse("accounts:login")
        response = self.client.post(url, {"email": "carla@example.com", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeEndpointTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="dan@example.com", password="Sup3rSecret!", first_name="Dan", last_name="Sow"
        )

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("accounts:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "dan@example.com")


class LogoutTests(APITestCase):
    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(
            email="eve@example.com", password="Sup3rSecret!", first_name="Eve", last_name="Diallo"
        )
        login_response = self.client.post(
            reverse("accounts:login"), {"email": "eve@example.com", "password": "Sup3rSecret!"}, format="json"
        )
        refresh = login_response.data["refresh"]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse("accounts:logout"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Le même refresh token ne doit plus permettre d'obtenir un nouvel access token.
        refresh_response = self.client.post(reverse("accounts:refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
