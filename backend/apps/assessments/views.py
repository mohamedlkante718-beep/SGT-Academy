import random

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.learning.permissions import user_has_access_to_course

from .models import Exam, ExamAttempt, Quiz, QuizAttempt
from .serializers import (
    ExamAttemptResultSerializer,
    ExamSubmitSerializer,
    QuestionPublicSerializer,
    QuizAttemptResultSerializer,
    QuizPublicSerializer,
    QuizSubmitSerializer,
)
from .services import grade_exam_attempt, grade_quiz_attempt


class QuizDetailView(APIView):
    """GET /api/v1/quizzes/{id}/ — questions d'un quiz, sans les bonnes réponses (§17)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        if not user_has_access_to_course(request.user, quiz.module.course):
            raise PermissionDenied("Vous n'avez pas accès à ce quiz.")
        return Response(QuizPublicSerializer(quiz).data)


class QuizSubmitView(APIView):
    """POST /api/v1/quizzes/{id}/submit — corrige immédiatement et renvoie le score (§17)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        if not user_has_access_to_course(request.user, quiz.module.course):
            raise PermissionDenied("Vous n'avez pas accès à ce quiz.")

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submissions_by_question_id = {
            str(a["question_id"]): a for a in serializer.validated_data["answers"]
        }

        attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
        attempt = grade_quiz_attempt(attempt, submissions_by_question_id)
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["score_percent", "passed", "submitted_at", "updated_at"])

        return Response(QuizAttemptResultSerializer(attempt).data, status=status.HTTP_201_CREATED)


class ExamStartView(APIView):
    """POST /api/v1/exams/{id}/start — démarre une tentative d'examen final (§18)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        if not user_has_access_to_course(request.user, exam.course):
            raise PermissionDenied("Vous n'avez pas accès à cet examen.")

        attempts_count = ExamAttempt.objects.filter(user=request.user, exam=exam).count()
        if attempts_count >= exam.max_attempts:
            raise ValidationError("Nombre maximal de tentatives atteint pour cet examen.")

        attempt = ExamAttempt.objects.create(
            user=request.user, exam=exam, attempt_number=attempts_count + 1
        )

        questions = list(exam.questions.prefetch_related("answers"))
        if exam.randomize_questions:
            random.shuffle(questions)

        data = {
            "id": str(exam.id),
            "title": exam.title,
            "num_questions": exam.num_questions,
            "duration_minutes": exam.duration_minutes,
            "max_attempts": exam.max_attempts,
            "pass_score_percent": exam.pass_score_percent,
            "questions": QuestionPublicSerializer(questions, many=True).data,
            "attempt_id": str(attempt.id),
            "deadline": attempt.started_at + timezone.timedelta(minutes=exam.duration_minutes),
        }
        return Response(data, status=status.HTTP_201_CREATED)


class ExamSubmitView(APIView):
    """POST /api/v1/exams/{id}/submit — corrige l'examen ; déclenche le certificat si réussi (§18/§19)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        exam = get_object_or_404(Exam, pk=pk)
        serializer = ExamSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        attempt = get_object_or_404(
            ExamAttempt, pk=serializer.validated_data["attempt_id"], exam=exam, user=request.user
        )
        if attempt.submitted_at:
            raise ValidationError("Cette tentative a déjà été soumise.")

        deadline = attempt.started_at + timezone.timedelta(minutes=exam.duration_minutes)
        if timezone.now() > deadline:
            attempt.submitted_at = timezone.now()
            attempt.score_percent = 0
            attempt.passed = False
            attempt.save(update_fields=["submitted_at", "score_percent", "passed", "updated_at"])
            raise ValidationError("Temps écoulé : la tentative est enregistrée comme échouée.")

        submissions_by_question_id = {
            str(a["question_id"]): a for a in serializer.validated_data["answers"]
        }
        attempt = grade_exam_attempt(attempt, submissions_by_question_id)
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=["score_percent", "passed", "submitted_at", "updated_at"])

        if attempt.passed and exam.course.certificate_available:
            from apps.certificates.services import issue_certificate

            issue_certificate(request.user, exam.course)

        return Response(ExamAttemptResultSerializer(attempt).data)
