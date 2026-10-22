from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction

from .forms import ProducteurAdminForm
from .models import Depense, Fiche, LigneEffectif, LigneValeur, Pret, Producteur, Vente

admin.site.site_header = "Suivi des producteurs — CIAF"
admin.site.site_title = "Suivi CIAF"
admin.site.index_title = "Administration"
admin.site.site_url = "/gestion/"


class PretInline(admin.TabularInline):
    model = Pret
    extra = 0


@admin.register(Producteur)
class ProducteurAdmin(admin.ModelAdmin):
    form = ProducteurAdminForm
    list_display = ["nom", "telephone", "volet", "actif", "ordre", "nombre_fiches", "derniere_fiche"]
    list_filter = ["volet", "actif"]
    list_editable = ["ordre"]
    search_fields = ["nom", "telephone"]
    inlines = [PretInline]
    fieldsets = [
        (None, {"fields": ["nom", "volet", "actif", "ordre"]}),
        ("Accès au téléphone", {"fields": ["telephone", "code_pin"],
                                "description": "Le producteur se connecte avec ce numéro et ce code PIN."}),
    ]

    @admin.display(description="fiches")
    def nombre_fiches(self, obj):
        return obj.fiches.count()

    @admin.display(description="dernière fiche")
    def derniere_fiche(self, obj):
        f = obj.fiches.order_by("-semaine").first()
        return f"{f.semaine:%d/%m/%Y}" if f else "—"

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        """Crée ou met à jour le compte de connexion du producteur (identifiant = téléphone)."""
        User = get_user_model()
        user = obj.utilisateur
        if user is None:
            user = User(username=obj.telephone)
        user.username = obj.telephone
        user.first_name = obj.nom[:150]
        user.is_active = obj.actif
        pin = form.cleaned_data.get("code_pin")
        if pin:
            user.set_password(pin)
        user.save()
        obj.utilisateur = user
        super().save_model(request, obj, form, change)


class EffectifInline(admin.TabularInline):
    model = LigneEffectif
    extra = 0


class ValeurInline(admin.TabularInline):
    model = LigneValeur
    extra = 0


class DepenseInline(admin.TabularInline):
    model = Depense
    extra = 0


class VenteInline(admin.TabularInline):
    model = Vente
    extra = 0


@admin.register(Fiche)
class FicheAdmin(admin.ModelAdmin):
    list_display = ["producteur", "semaine", "valeur_totale", "depenses", "ventes", "modifie_le", "saisie_par"]
    list_filter = ["semaine", "producteur__volet", "producteur"]
    date_hierarchy = "semaine"
    inlines = [EffectifInline, ValeurInline, DepenseInline, VenteInline]
    readonly_fields = ["saisie_par", "modifie_le"]

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
