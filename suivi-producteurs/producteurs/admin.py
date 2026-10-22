from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction

from .forms import ProducteurAdminForm, ResponsableAdminForm
from .models import (Depense, Fiche, LigneEffectif, LigneValeur, Pret, Producteur, Produit, Responsable,
                     Secteur, Vente)

admin.site.site_header = "Suivi des producteurs — CIAF"
admin.site.site_title = "Suivi CIAF"
admin.site.index_title = "Administration"
admin.site.site_url = "/gestion/"


class CompteTelephoneAdmin(admin.ModelAdmin):
    """Crée ou met à jour le compte de connexion (identifiant = téléphone, mot de passe = code PIN)."""

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        user = obj.utilisateur or get_user_model()(username=obj.telephone)
        user.username = obj.telephone
        user.first_name = obj.nom[:150]
        user.is_active = obj.actif
        if form.cleaned_data.get("code_pin"):
            user.set_password(form.cleaned_data["code_pin"])
        user.save()
        obj.utilisateur = user
        super().save_model(request, obj, form, change)


class ProduitInline(admin.TabularInline):
    model = Produit
    extra = 3
    fields = ["nom", "unite", "compter", "valoriser", "ordre", "actif"]


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ["nom", "nombre_produits", "actif", "ordre"]
    list_editable = ["ordre"]
    inlines = [ProduitInline]

    @admin.display(description="produits")
    def nombre_produits(self, obj):
        return obj.produits.filter(actif=True).count()


class PretInline(admin.TabularInline):
    model = Pret
    extra = 0


@admin.register(Producteur)
class ProducteurAdmin(CompteTelephoneAdmin):
    form = ProducteurAdminForm
    list_display = ["nom", "telephone", "responsable", "nombre_produits", "actif", "ordre", "derniere_fiche"]
    list_filter = ["responsable", "produits__secteur", "actif"]
    list_editable = ["ordre"]
    search_fields = ["nom", "telephone"]
    inlines = [PretInline]
    fieldsets = [
        (None, {"fields": ["nom", "responsable", "actif", "ordre"]}),
        ("Produits", {"fields": ["produits"]}),
        ("Accès au téléphone", {"fields": ["telephone", "code_pin"],
                                "description": "Le producteur se connecte avec ce numéro et ce code PIN."}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("responsable").prefetch_related("produits")

    @admin.display(description="produits")
    def nombre_produits(self, obj):
        return len(obj.produits.all())

    @admin.display(description="dernière fiche")
    def derniere_fiche(self, obj):
        f = obj.fiches.order_by("-semaine").first()
        return f"{f.semaine:%d/%m/%Y} ({f.get_statut_display().lower()})" if f else "—"


@admin.register(Responsable)
class ResponsableAdmin(CompteTelephoneAdmin):
    form = ResponsableAdminForm
    list_display = ["nom", "telephone", "nombre_producteurs", "actif"]
    fieldsets = [
        (None, {"fields": ["nom", "actif", "producteurs"]}),
        ("Accès", {"fields": ["telephone", "code_pin"],
                   "description": "Le responsable se connecte avec ce numéro et ce code PIN. "
                                  "Il voit ses producteurs et valide leurs fiches, sans pouvoir les modifier."}),
    ]

    @admin.display(description="producteurs")
    def nombre_producteurs(self, obj):
        return obj.producteurs.count()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        choisis = form.cleaned_data.get("producteurs") or []
        obj.producteurs.exclude(pk__in=[p.pk for p in choisis]).update(responsable=None)
        Producteur.objects.filter(pk__in=[p.pk for p in choisis]).update(responsable=obj)


class EffectifInline(admin.TabularInline):
    model = LigneEffectif
    extra = 0
    fields = ["produit", "libelle", "quantite"]


class ValeurInline(admin.TabularInline):
    model = LigneValeur
    extra = 0
    fields = ["produit", "libelle", "montant"]


class DepenseInline(admin.TabularInline):
    model = Depense
    extra = 0


class VenteInline(admin.TabularInline):
    model = Vente
    extra = 0


@admin.register(Fiche)
class FicheAdmin(admin.ModelAdmin):
    list_display = ["producteur", "semaine", "statut", "valeur_totale", "depenses", "ventes", "modifie_le"]
    list_filter = ["statut", "semaine", "producteur__responsable", "producteur"]
    date_hierarchy = "semaine"
    inlines = [EffectifInline, ValeurInline, DepenseInline, VenteInline]
    fields = ["producteur", "semaine", "observations", "statut", "commentaire", "valide_par", "valide_le",
              "saisie_par", "modifie_le"]
    readonly_fields = ["valide_par", "valide_le", "saisie_par", "modifie_le"]

    @admin.display(description="valeur totale (F)")
    def valeur_totale(self, obj):
        return obj.total_valeurs

    @admin.display(description="dépenses (F)")
    def depenses(self, obj):
        return obj.total_depenses

    @admin.display(description="ventes (F)")
    def ventes(self, obj):
        return obj.total_ventes

    def save_model(self, request, obj, form, change):
        if not obj.saisie_par_id:
            obj.saisie_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(Pret)
class PretAdmin(admin.ModelAdmin):
    list_display = ["producteur", "date", "type", "montant", "description"]
    list_filter = ["type", "producteur"]
    date_hierarchy = "date"
