from django.contrib import admin

from .models import Answer, Exam, ExamAttempt, Question, Quiz, QuizAttempt, QuizResult


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "pass_score_percent")
    inlines = [QuestionInline]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "num_questions", "duration_minutes", "max_attempts", "pass_score_percent")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "exam", "question_type", "points")
    inlines = [AnswerInline]


admin.site.register(QuizAttempt)
admin.site.register(QuizResult)
admin.site.register(ExamAttempt)
