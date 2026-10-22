from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from producteurs import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("saisie/", views.saisie, name="saisie"),
    path("saisie/<str:semaine>/", views.saisie, name="saisie_semaine"),
    path("gestion/", views.tableau, name="tableau"),
    path("gestion/producteur/<int:pk>/", views.fiche_producteur, name="fiche_producteur"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("admin/", admin.site.urls),
]
