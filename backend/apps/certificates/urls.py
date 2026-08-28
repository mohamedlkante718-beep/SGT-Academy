from django.urls import path

from .views import CertificateDetailView, CertificateVerifyView, MyCertificatesView

app_name = "certificates"

urlpatterns = [
    path("certificates/", MyCertificatesView.as_view(), name="my-certificates"),
    path("certificates/<uuid:pk>/", CertificateDetailView.as_view(), name="certificate-detail"),
    path("certificates/verify/<str:code>/", CertificateVerifyView.as_view(), name="certificate-verify"),
]
