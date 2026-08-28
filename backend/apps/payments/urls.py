from django.urls import path

from .views import PaymentStatusView, PurchaseView, SubmitManualProofView

app_name = "payments"

urlpatterns = [
    path("courses/<slug:slug>/purchase/", PurchaseView.as_view(), name="purchase"),
    path("payments/<str:reference>/", PaymentStatusView.as_view(), name="status"),
    path("payments/<str:reference>/proof/", SubmitManualProofView.as_view(), name="manual-proof"),
]
