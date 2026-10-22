from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.static import serve

from producteurs import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("saisie/", views.saisie, name="saisie"),
    path("saisie/<str:semaine>/", views.saisie, name="saisie_semaine"),
    path("gestion/", views.tableau, name="tableau"),
    path("gestion/producteur/<int:pk>/", views.fiche_producteur, name="fiche_producteur"),
    path("gestion/rapport/", views.rapport, name="rapport"),
    path("gestion/rapport/imprimer/", views.rapport_imprimable, name="rapport_imprimable"),
    path("gestion/rapport/excel/", views.rapport_excel, name="rapport_excel"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("admin/", admin.site.urls),
]

# Sert les fichiers de style et les images directement depuis Django, au cas où le réglage
# « Static files » de l'hébergeur n'est pas fait (sinon c'est l'hébergeur qui les sert, plus vite).
urlpatterns += [re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT})]
