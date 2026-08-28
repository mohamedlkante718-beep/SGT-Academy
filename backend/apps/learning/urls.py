from django.urls import path

from .views import CourseProgressView, LessonCompleteView, MyCoursesView

app_name = "learning"

urlpatterns = [
    path("my-courses/", MyCoursesView.as_view(), name="my-courses"),
    path("courses/<slug:slug>/progress/", CourseProgressView.as_view(), name="course-progress"),
    path("lessons/<uuid:lesson_id>/complete/", LessonCompleteView.as_view(), name="lesson-complete"),
]
