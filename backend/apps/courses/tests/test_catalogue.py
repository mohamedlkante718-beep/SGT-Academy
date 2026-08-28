from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course


class CourseCatalogueTests(APITestCase):
    def setUp(self):
        self.published = Course.objects.create(
            title="QGIS pour débutants",
            short_description="Introduction à QGIS",
            price=25000,
            currency="XOF",
            status=Course.PUBLISHED,
        )
        self.draft = Course.objects.create(
            title="Formation en préparation",
            price=15000,
            currency="XOF",
            status=Course.DRAFT,
        )

    def test_list_is_public_and_only_shows_published_courses(self):
        response = self.client.get(reverse("courses:course-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [c["slug"] for c in response.data["results"]]
        self.assertIn(self.published.slug, slugs)
        self.assertNotIn(self.draft.slug, slugs)

    def test_detail_of_published_course_is_accessible(self):
        response = self.client.get(reverse("courses:course-detail", args=[self.published.slug]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "QGIS pour débutants")

    def test_detail_of_draft_course_is_not_accessible(self):
        response = self.client.get(reverse("courses:course-detail", args=[self.draft.slug]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_price_filter(self):
        response = self.client.get(reverse("courses:course-list"), {"max_price": 20000})
        slugs = [c["slug"] for c in response.data["results"]]
        self.assertNotIn(self.published.slug, slugs)
