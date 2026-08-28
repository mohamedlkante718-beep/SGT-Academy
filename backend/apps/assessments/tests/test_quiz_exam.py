from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.courses.models import Course, Module
from apps.learning.models import Enrollment

from ..models import Answer, Exam, Question, Quiz


class QuizTests(APITestCase):
    def setUp(self):
        self.course = Course.objects.create(title="Formation Quiz", price=1000, status=Course.PUBLISHED)
        self.module = Module.objects.create(course=self.course, title="Module 1", order=1)
        self.quiz = Quiz.objects.create(module=self.module, title="Quiz 1", pass_score_percent=70)

        self.q1 = Question.objects.create(
            quiz=self.quiz, text="2+2=?", question_type=Question.MULTIPLE_CHOICE, points=1, order=1
        )
        self.q1_correct = Answer.objects.create(question=self.q1, text="4", is_correct=True, order=1)
        Answer.objects.create(question=self.q1, text="5", is_correct=False, order=2)

        self.q2 = Question.objects.create(
            quiz=self.quiz, text="Le ciel est bleu ?", question_type=Question.TRUE_FALSE, points=1, order=2
        )
        self.q2_correct = Answer.objects.create(question=self.q2, text="Vrai", is_correct=True, order=1)
        Answer.objects.create(question=self.q2, text="Faux", is_correct=False, order=2)

        self.user = User.objects.create_user(
            email="quiz@example.com", password="Sup3rSecret!", first_name="Qui", last_name="Z"
        )
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)

    def test_quiz_detail_hides_correct_answers(self):
        response = self.client.get(reverse("assessments:quiz-detail", args=[self.quiz.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for question in response.data["questions"]:
            for answer in question["answers"]:
                self.assertNotIn("is_correct", answer)

    def test_submit_all_correct_passes(self):
        payload = {
            "answers": [
                {"question_id": str(self.q1.id), "answer_id": str(self.q1_correct.id)},
                {"question_id": str(self.q2.id), "answer_id": str(self.q2_correct.id)},
            ]
        }
        response = self.client.post(
            reverse("assessments:quiz-submit", args=[self.quiz.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["score_percent"], 100)
        self.assertTrue(response.data["passed"])

    def test_submit_all_wrong_fails(self):
        payload = {"answers": [{"question_id": str(self.q1.id), "answer_id": None}]}
        response = self.client.post(
            reverse("assessments:quiz-submit", args=[self.quiz.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["score_percent"], 0)
        self.assertFalse(response.data["passed"])

    def test_non_enrolled_user_cannot_access_quiz(self):
        stranger = User.objects.create_user(
            email="stranger@example.com", password="Sup3rSecret!", first_name="Str", last_name="Anger"
        )
        self.client.force_authenticate(user=stranger)
        response = self.client.get(reverse("assessments:quiz-detail", args=[self.quiz.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ExamAndCertificateTests(APITestCase):
    def setUp(self):
        self.course = Course.objects.create(
            title="Formation Examen", price=1000, status=Course.PUBLISHED,
            duration_hours=10, certificate_available=True,
        )
        self.exam = Exam.objects.create(
            course=self.course, title="Examen final", num_questions=1,
            duration_minutes=30, max_attempts=2, pass_score_percent=50,
        )
        self.question = Question.objects.create(
            exam=self.exam, text="1+1=?", question_type=Question.MULTIPLE_CHOICE, points=1, order=1
        )
        self.correct = Answer.objects.create(question=self.question, text="2", is_correct=True, order=1)
        Answer.objects.create(question=self.question, text="3", is_correct=False, order=2)

        self.user = User.objects.create_user(
            email="exam@example.com", password="Sup3rSecret!", first_name="Ex", last_name="Am"
        )
        Enrollment.objects.create(user=self.user, course=self.course)
        self.client.force_authenticate(user=self.user)

    def _start_attempt(self):
        response = self.client.post(reverse("assessments:exam-start", args=[self.exam.id]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["attempt_id"]

    def test_passing_exam_issues_certificate(self):
        attempt_id = self._start_attempt()
        payload = {
            "attempt_id": attempt_id,
            "answers": [{"question_id": str(self.question.id), "answer_id": str(self.correct.id)}],
        }
        response = self.client.post(
            reverse("assessments:exam-submit", args=[self.exam.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["passed"])

        cert_response = self.client.get(reverse("certificates:my-certificates"))
        self.assertEqual(len(cert_response.data["results"]), 1)
        self.assertTrue(cert_response.data["results"][0]["code"].startswith("SGT-"))

    def test_max_attempts_enforced(self):
        for _ in range(2):
            attempt_id = self._start_attempt()
            self.client.post(
                reverse("assessments:exam-submit", args=[self.exam.id]),
                {"attempt_id": attempt_id, "answers": []},
                format="json",
            )
        response = self.client.post(reverse("assessments:exam-start", args=[self.exam.id]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_submit_same_attempt_twice(self):
        attempt_id = self._start_attempt()
        payload = {"attempt_id": attempt_id, "answers": []}
        first = self.client.post(
            reverse("assessments:exam-submit", args=[self.exam.id]), payload, format="json"
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        second = self.client.post(
            reverse("assessments:exam-submit", args=[self.exam.id]), payload, format="json"
        )
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
