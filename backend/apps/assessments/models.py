from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course, Module


class Quiz(TimeStampedModel):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name="quiz", verbose_name="module")
    title = models.CharField(max_length=200, verbose_name="titre")
    pass_score_percent = models.PositiveSmallIntegerField(default=70, verbose_name="score de réussite (%)")

    class Meta:
        verbose_name = "quiz"
        verbose_name_plural = "quiz"

    def __str__(self):
        return self.title


class Exam(TimeStampedModel):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name="exam", verbose_name="formation")
    title = models.CharField(max_length=200, verbose_name="titre")
    num_questions = models.PositiveSmallIntegerField(default=20, verbose_name="nombre de questions")
    duration_minutes = models.PositiveSmallIntegerField(default=30, verbose_name="durée (minutes)")
    max_attempts = models.PositiveSmallIntegerField(default=3, verbose_name="tentatives maximum")
    pass_score_percent = models.PositiveSmallIntegerField(default=70, verbose_name="score de réussite (%)")
    randomize_questions = models.BooleanField(default=True, verbose_name="questions aléatoires")

    class Meta:
        verbose_name = "examen"
        verbose_name_plural = "examens"

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
    quiz = models.ForeignKey(
        Quiz, null=True, blank=True, on_delete=models.CASCADE, related_name="questions", verbose_name="quiz"
    )
    exam = models.ForeignKey(
        Exam, null=True, blank=True, on_delete=models.CASCADE, related_name="questions", verbose_name="examen"
    )

    text = models.TextField(verbose_name="texte")
    question_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default=MULTIPLE_CHOICE, verbose_name="type de question"
    )
    explanation = models.TextField(blank=True, verbose_name="explication")
    points = models.PositiveSmallIntegerField(default=1, verbose_name="points")
    order = models.PositiveIntegerField(default=0, verbose_name="ordre")

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
        verbose_name = "question"
        verbose_name_plural = "questions"

    def __str__(self):
        return self.text[:80]


class Answer(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="question")
    text = models.CharField(max_length=500, verbose_name="texte")
    is_correct = models.BooleanField(default=False, verbose_name="correcte")
    order = models.PositiveIntegerField(default=0, verbose_name="ordre")

    class Meta:
        ordering = ["order"]
        verbose_name = "réponse"
        verbose_name_plural = "réponses"

    def __str__(self):
        return self.text


class QuizAttempt(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts", verbose_name="utilisateur"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="quiz")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="commencé le")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="soumis le")
    score_percent = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="score (%)")
    passed = models.BooleanField(null=True, verbose_name="réussi")

    class Meta:
        verbose_name = "tentative de quiz"
        verbose_name_plural = "tentatives de quiz"

    def __str__(self):
        return f"{self.user} — {self.quiz} ({self.score_percent}%)"


class QuizResult(TimeStampedModel):
    """Réponse donnée par l'apprenant à une question, pour une tentative donnée."""

    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="results", verbose_name="tentative"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="question")
    selected_answer = models.ForeignKey(
        Answer, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="réponse sélectionnée"
    )
    short_answer_text = models.CharField(max_length=500, blank=True, verbose_name="réponse courte")
    is_correct = models.BooleanField(default=False, verbose_name="correcte")
    points_awarded = models.PositiveSmallIntegerField(default=0, verbose_name="points obtenus")

    class Meta:
        verbose_name = "résultat de quiz"
        verbose_name_plural = "résultats de quiz"


class ExamAttempt(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exam_attempts", verbose_name="utilisateur"
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="attempts", verbose_name="examen")
    attempt_number = models.PositiveSmallIntegerField(default=1, verbose_name="numéro de tentative")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="commencé le")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="soumis le")
    score_percent = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="score (%)")
    passed = models.BooleanField(null=True, verbose_name="réussi")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "exam", "attempt_number"], name="unique_exam_attempt_number"),
        ]
        verbose_name = "tentative d'examen"
        verbose_name_plural = "tentatives d'examen"

    def __str__(self):
        return f"{self.user} — {self.exam} #{self.attempt_number}"
