from django.urls import path

from .views import CourseDetailView, CourseListView

app_name = "courses"

urlpatterns = [
    path("", CourseListView.as_view(), name="course-list"),
    path("<slug:slug>/", CourseDetailView.as_view(), name="course-detail"),
]
