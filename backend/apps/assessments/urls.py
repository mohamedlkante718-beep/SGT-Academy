from django.urls import path

from .views import ExamStartView, ExamSubmitView, QuizDetailView, QuizSubmitView

app_name = "assessments"

urlpatterns = [
    path("quizzes/<uuid:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
    path("quizzes/<uuid:pk>/submit/", QuizSubmitView.as_view(), name="quiz-submit"),
    path("exams/<uuid:pk>/start/", ExamStartView.as_view(), name="exam-start"),
    path("exams/<uuid:pk>/submit/", ExamSubmitView.as_view(), name="exam-submit"),
]
