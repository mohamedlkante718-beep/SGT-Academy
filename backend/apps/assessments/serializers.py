from rest_framework import serializers

from .models import Answer, Exam, ExamAttempt, Question, Quiz, QuizAttempt


class AnswerPublicSerializer(serializers.ModelSerializer):
    """Ne renvoie jamais is_correct à l'apprenant avant correction (§17)."""

    class Meta:
        model = Answer
        fields = ["id", "text", "order"]


class QuestionPublicSerializer(serializers.ModelSerializer):
    answers = AnswerPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "question_type", "points", "order", "answers"]


class QuizPublicSerializer(serializers.ModelSerializer):
    questions = QuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "pass_score_percent", "questions"]


class ExamPublicSerializer(serializers.ModelSerializer):
    questions = QuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = [
            "id", "title", "num_questions", "duration_minutes",
            "max_attempts", "pass_score_percent", "questions",
        ]


class AnswerSubmissionSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    answer_id = serializers.UUIDField(required=False, allow_null=True)
    text = serializers.CharField(required=False, allow_blank=True)


class QuizSubmitSerializer(serializers.Serializer):
    answers = AnswerSubmissionSerializer(many=True)


class QuizAttemptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ["id", "score_percent", "passed", "submitted_at"]


class ExamSubmitSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    answers = AnswerSubmissionSerializer(many=True)


class ExamAttemptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = ["id", "attempt_number", "score_percent", "passed", "submitted_at"]
