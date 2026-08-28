from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course, Module


class Quiz(TimeStampedModel):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name="quiz")
    title = models.CharField(max_length=200)
    pass_score_percent = models.PositiveSmallIntegerField(default=70)

    def __str__(self):
        return self.title


class Exam(TimeStampedModel):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="exam")
    title = models.CharField(max_length=200)
    num_questions = models.PositiveSmallIntegerField(default=20)
    duration_minutes = models.PositiveSmallIntegerField(default=30)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    pass_score_percent = models.PositiveSmallIntegerField(default=70)
    randomize_questions = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Question(TimeStampedModel):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE = "TRUE_FALSE"
    SHORT_ANSWER = "SHORT_ANSWER"
    TYPE_CHOICES = [
        (MULTIPLE_CHOICE, "Choix multiple"),
        (TRUE_FALSE, "Vrai / Faux"),
        (SHORT_ANSWER, "Réponse courte"),
    ]

    # Une question appartient à un quiz OU à un examen, jamais les deux.
    quiz = models.ForeignKey(Quiz, null=True, blank=True, on_delete=models.CASCADE, related_name="questions")
    exam = models.ForeignKey(Exam, null=True, blank=True, on_delete=models.CASCADE, related_name="questions")

    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=MULTIPLE_CHOICE)
    explanation = models.TextField(blank=True)
    points = models.PositiveSmallIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(quiz__isnull=False, exam__isnull=True)
                    | models.Q(quiz__isnull=True, exam__isnull=False)
                ),
                name="question_belongs_to_quiz_xor_exam",
            )
        ]

    def __str__(self):
        return self.text[:80]


class Answer(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class QuizAttempt(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    passed = models.BooleanField(null=True)

    def __str__(self):
        return f"{self.user} — {self.quiz} ({self.score_percent}%)"


class QuizResult(TimeStampedModel):
    """Réponse donnée par l'apprenant à une question, pour une tentative donnée."""

    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="results")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, null=True, blank=True, on_delete=models.SET_NULL)
    short_answer_text = models.CharField(max_length=500, blank=True)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveSmallIntegerField(default=0)


class ExamAttempt(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_attempts")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField(default=1)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score_percent = models.PositiveSmallIntegerField(null=True, blank=True)
    passed = models.BooleanField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "exam", "attempt_number"], name="unique_exam_attempt_number"),
        ]

    def __str__(self):
        return f"{self.user} — {self.exam} #{self.attempt_number}"
