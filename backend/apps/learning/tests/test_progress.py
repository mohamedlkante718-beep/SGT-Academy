from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.courses.models import Course, Lesson, Module

from ..models import CourseProgress, Enrollment


class LessonAccessTests(APITestCase):
    def setUp(self):
        self.course = Course.objects.create(title="Formation SIG", price=10000, status=Course.PUBLISHED)
        self.module = Module.objects.create(course=self.course, title="Module 1", order=1)
        self.preview_lesson = Lesson.objects.create(
            module=self.module, title="Introduction", order=1, is_preview=True
        )
        self.locked_lesson = Lesson.objects.create(
            module=self.module, title="Approfondissement", order=2, is_preview=False
        )

        self.user = User.objects.create_user(
            email="student@example.com", password="Sup3rSecret!", first_name="Stu", last_name="Dent"
        )
        self.client.force_authenticate(user=self.user)

    def test_can_complete_preview_lesson_without_enrollment(self):
        url = reverse("learning:lesson-complete", args=[self.preview_lesson.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_complete_locked_lesson_without_enrollment(self):
        url = reverse("learning:lesson-complete", args=[self.locked_lesson.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_can_complete_locked_lesson_once_enrolled(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        url = reverse("learning:lesson-complete", args=[self.locked_lesson.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_course_progress_updates_on_completion(self):
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.post(reverse("learning:lesson-complete", args=[self.preview_lesson.id]))
        progress = CourseProgress.objects.get(user=self.user, course=self.course)
        self.assertEqual(progress.percent_complete, 50)  # 1 leçon sur 2

        self.client.post(reverse("learning:lesson-complete", args=[self.locked_lesson.id]))
        progress.refresh_from_db()
        self.assertEqual(progress.percent_complete, 100)
        self.assertIsNotNone(progress.completed_at)

    def test_course_progress_view_requires_enrollment(self):
        url = reverse("learning:course-progress", args=[self.course.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        Enrollment.objects.create(user=self.user, course=self.course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data[0]["lessons"]), 2)


class MyCoursesTests(APITestCase):
    def test_my_courses_lists_only_own_enrollments(self):
        course = Course.objects.create(title="Formation X", price=1000, status=Course.PUBLISHED)
        user_a = User.objects.create_user(email="a@example.com", password="x", first_name="A", last_name="A")
        user_b = User.objects.create_user(email="b@example.com", password="x", first_name="B", last_name="B")
        Enrollment.objects.create(user=user_a, course=course)

        self.client.force_authenticate(user=user_b)
        response = self.client.get(reverse("learning:my-courses"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

        self.client.force_authenticate(user=user_a)
        response = self.client.get(reverse("learning:my-courses"))
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["course_slug"], course.slug)
