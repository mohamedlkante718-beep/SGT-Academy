from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.static import serve

from producteurs import gestion, views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", views.ConnexionView.as_view(), name="connexion"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),
    path("saisie/", views.saisie, name="saisie"),
    path("saisie/<str:semaine>/", views.saisie, name="saisie_semaine"),
    path("saisie/<str:semaine>/supprimer/", views.saisie_supprimer, name="saisie_supprimer"),
    path("mes-semaines/", views.mes_semaines, name="mes_semaines"),
    path("gestion/", views.tableau, name="tableau"),
    path("gestion/producteur/<int:pk>/", views.fiche_producteur, name="fiche_producteur"),
    path("gestion/producteur/<int:pk>/semaines/", views.semaines_producteur, name="semaines_producteur"),
    path("gestion/producteur/<int:pk>/saisie/<str:semaine>/", views.saisie_admin, name="saisie_admin"),
    path("gestion/producteurs/", gestion.producteurs, name="producteurs"),
    path("gestion/producteurs/ajouter/", gestion.producteur_form, name="producteur_ajouter"),
    path("gestion/producteurs/<int:pk>/modifier/", gestion.producteur_form, name="producteur_modifier"),
    path("gestion/responsables/", gestion.responsables, name="responsables"),
    path("gestion/responsables/ajouter/", gestion.responsable_form, name="responsable_ajouter"),
    path("gestion/responsables/<int:pk>/modifier/", gestion.responsable_form, name="responsable_modifier"),
    path("gestion/secteurs/", gestion.secteurs, name="secteurs"),
    path("gestion/secteurs/ajouter/", gestion.secteur_form, name="secteur_ajouter"),
    path("gestion/secteurs/<int:pk>/", gestion.secteur_form, name="secteur_modifier"),
    path("gestion/fiches/<int:pk>/finances/", gestion.finances, name="finances"),
    path("gestion/fiches/<int:pk>/supprimer/", gestion.fiche_supprimer, name="fiche_supprimer"),
    path("gestion/prets/", gestion.prets, name="prets"),
    path("gestion/caisse/", gestion.caisse, name="caisse"),
    path("gestion/rapport/", views.rapport, name="rapport"),
    path("gestion/rapport/imprimer/", views.rapport_imprimable, name="rapport_imprimable"),
    path("gestion/rapport/excel/", views.rapport_excel, name="rapport_excel"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
    path(settings.ADMIN_URL, admin.site.urls),
]

# Sert les fichiers de style et les images directement depuis Django, au cas où le réglage
# « Static files » de l'hébergeur n'est pas fait (sinon c'est l'hébergeur qui les sert, plus vite).
urlpatterns += [
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(r"^media/(?P<path>.*)$", lambda request, path: serve(request, path, document_root=settings.MEDIA_ROOT)),
]
