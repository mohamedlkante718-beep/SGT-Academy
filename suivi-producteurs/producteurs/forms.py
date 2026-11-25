from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.forms import inlineformset_factory

from .models import (CategorieCaisse, Depense, Fiche, OperationCaisse, Pret, Producteur, Produit, Responsable,
                     Secteur, Vente)


def normaliser_telephone(valeur):
    """Garde uniquement les chiffres (et un + initial) : « 76 12 34 56 » → « 76123456 »."""
    valeur = (valeur or "").strip()
    signe = "+" if valeur.startswith("+") else ""
    return signe + "".join(c for c in valeur if c.isdigit())


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(label="Téléphone", widget=forms.TextInput(attrs={
        "autocomplete": "username", "inputmode": "tel", "autofocus": True}))
    password = forms.CharField(label="Code PIN", strip=False, widget=forms.PasswordInput(attrs={
        "autocomplete": "current-password", "inputmode": "numeric"}))

    error_messages = {
        "invalid_login": "Téléphone ou code PIN incorrect. Vérifiez et réessayez.",
        "inactive": "Ce compte est désactivé. Contactez l'administrateur du CIAF/CE.",
    }

    def clean(self):
        from .securite import adresse_ip, est_bloque, noter
        identifiant = self.cleaned_data.get("username")
        ip = adresse_ip(self.request) if self.request else None
        if est_bloque(identifiant, ip):
            raise forms.ValidationError(
                "Trop d'essais avec un code faux. Par sécurité, la connexion est bloquée pendant "
                f"{settings.CONNEXION_BLOCAGE_MINUTES} minutes. Réessayez plus tard ou demandez un nouveau code "
                "à l'administrateur.", code="bloque")
        try:
            resultat = super().clean()
        except forms.ValidationError:
            noter(identifiant, ip, reussie=False)
            raise
        noter(identifiant, ip, reussie=True)
        return resultat

    def clean_username(self):
        brut = self.cleaned_data["username"].strip()
        # Les administrateurs se connectent avec leur nom d'utilisateur, les autres avec leur numéro.
        tel = normaliser_telephone(brut)
        return tel if tel and len(tel) >= 6 and tel.lstrip("+").isdigit() else brut


def lier_compte(obj, pin=None):
    """Crée ou met à jour le compte de connexion d'un producteur ou d'un responsable
    (identifiant = téléphone, mot de passe = code PIN). L'objet doit ensuite être enregistré."""
    user = obj.utilisateur or get_user_model()(username=obj.telephone)
    user.username = obj.telephone
    user.first_name = obj.nom[:150]
    user.is_active = obj.actif
    if pin:
        user.set_password(pin)
    elif not user.pk:
        user.set_unusable_password()
    user.save()
    obj.utilisateur = user


class CompteTelephoneForm(forms.ModelForm):
    """Téléphone + code PIN : partagé par les fiches Producteur et Responsable de l'administration."""

    code_pin = forms.CharField(
        label="Code PIN", required=False, min_length=4, max_length=6,
        help_text="4 à 6 chiffres, à communiquer à la personne. Laissez vide pour garder le code actuel.",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
    )

    def clean_telephone(self):
        tel = normaliser_telephone(self.cleaned_data["telephone"])
        if len(tel.lstrip("+")) < 8:
            raise forms.ValidationError("Numéro trop court.")
        autre = get_user_model().objects.filter(username=tel).exclude(pk=self.instance.utilisateur_id).first()
        if autre:
            raise forms.ValidationError("Ce numéro est déjà utilisé par un autre compte.")
        return tel

    def clean_code_pin(self):
        pin = self.cleaned_data.get("code_pin", "").strip()
        if pin and not pin.isdigit():
            raise forms.ValidationError("Le code PIN ne contient que des chiffres.")
        return pin

    def clean(self):
        data = super().clean()
        if not self.instance.utilisateur_id and not data.get("code_pin"):
            self.add_error("code_pin", "Choisissez un code PIN pour que cette personne puisse se connecter.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            with transaction.atomic():
                lier_compte(obj, self.cleaned_data.get("code_pin"))
                obj.save()
                self.save_m2m()
                self.apres_enregistrement(obj)
        return obj

    def apres_enregistrement(self, obj):
        pass


class ProduitsParSecteur(forms.ModelMultipleChoiceField):
    """Cases à cocher des produits, regroupées par secteur."""

    widget = forms.CheckboxSelectMultiple

    def __init__(self, **kwargs):
        super().__init__(queryset=Produit.objects.filter(actif=True).select_related("secteur"), **kwargs)

    def grouper(self):
        groupes = {}
        for p in self.queryset:
            groupes.setdefault(p.secteur.nom, []).append((p.pk, str(p)))
        self.choices = list(groupes.items())


class ProducteurAdminForm(CompteTelephoneForm):
    field_order = ["nom", "telephone", "code_pin", "responsable", "produits", "actif", "ordre"]
    produits = ProduitsParSecteur(required=False, label="Produits attribués",
                                  help_text="Le producteur ne remplira que ces produits sur son téléphone.")

    class Meta:
        model = Producteur
        fields = ["nom", "telephone", "responsable", "produits", "actif", "ordre"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produits"].grouper()


class ResponsableAdminForm(CompteTelephoneForm):
    field_order = ["nom", "telephone", "code_pin", "producteurs", "actif"]
    producteurs = forms.ModelMultipleChoiceField(
        queryset=Producteur.objects.all(), required=False, widget=forms.CheckboxSelectMultiple,
        label="Producteurs suivis", help_text="Ce responsable verra et validera les fiches de ces producteurs.")

    class Meta:
        model = Responsable
        fields = ["nom", "telephone", "actif"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["producteurs"].initial = self.instance.producteurs.all()

    def apres_enregistrement(self, obj):
        choisis = [p.pk for p in self.cleaned_data.get("producteurs") or []]
        obj.producteurs.exclude(pk__in=choisis).update(responsable=None)
        Producteur.objects.filter(pk__in=choisis).update(responsable=obj)


class ValidationForm(forms.Form):
    decision = forms.ChoiceField(choices=[("valider", "Valider"), ("corriger", "Demander une correction")])
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={
        "rows": 2, "placeholder": "Ce qu'il faut corriger (obligatoire pour une demande de correction)"}))

    def clean(self):
        data = super().clean()
        if data.get("decision") == "corriger" and not data.get("commentaire", "").strip():
            self.add_error("commentaire", "Expliquez au producteur ce qu'il doit corriger.")
        return data


# ---------------------------------------------------------------- pages de gestion (administrateur)

DATE = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
MONTANT = forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "step": 1})


class SecteurForm(forms.ModelForm):
    class Meta:
        model = Secteur
        fields = ["nom", "ordre", "actif"]


ProduitsFormSet = inlineformset_factory(
    Secteur, Produit, fields=["nom", "unite", "compter", "valoriser", "ordre", "actif"], extra=3, can_delete=False,
    widgets={"ordre": forms.NumberInput(attrs={"min": 0, "style": "width:5em"})})

DepensesFormSet = inlineformset_factory(
    Fiche, Depense, extra=2, can_delete=True,
    fields=["date", "categorie", "description", "quantite", "prix_unitaire", "montant", "mode_paiement"],
    widgets={"date": DATE, "montant": MONTANT, "prix_unitaire": MONTANT,
             "quantite": forms.NumberInput(attrs={"inputmode": "decimal", "step": "any", "min": 0})})

VentesFormSet = inlineformset_factory(
    Fiche, Vente, extra=2, can_delete=True,
    fields=["date", "categorie", "description", "poids", "quantite", "prix_unitaire", "montant", "mode_paiement", "client"],
    widgets={"date": DATE, "montant": MONTANT, "prix_unitaire": MONTANT,
             "quantite": forms.NumberInput(attrs={"inputmode": "decimal", "step": "any", "min": 0})})


class ProducteursACocher(forms.ModelMultipleChoiceField):
    """Tous les producteurs en cases à cocher, ceux qui ne produisent plus compris (marqués)."""

    widget = forms.CheckboxSelectMultiple

    def __init__(self, **kwargs):
        super().__init__(queryset=Producteur.objects.order_by("-actif", "nom"), **kwargs)

    def label_from_instance(self, p):
        return p.nom if p.actif else f"{p.nom} (ne produit plus)"


class PretForm(forms.ModelForm):
    """Accorder un prêt ou une avance à un ou plusieurs producteurs : un prêt est créé pour chacun."""

    field_order = ["producteur", "date", "montant", "taux_interet", "echeance", "description"]
    producteur = ProducteursACocher(
        label="Producteurs", error_messages={"required": "Cochez au moins un producteur."},
        help_text="Cochez toutes les personnes qui reçoivent ce prêt. Chacune reçoit le montant indiqué.")

    class Meta:
        model = Pret
        # « producteur » (plusieurs cases à cocher) n'est pas un champ du modèle : save() crée un prêt par case.
        fields = ["date", "montant", "taux_interet", "echeance", "description"]
        widgets = {"date": DATE, "echeance": DATE, "montant": MONTANT,
                   "taux_interet": forms.NumberInput(attrs={"inputmode": "decimal", "step": "0.5", "min": 0}),
                   "description": forms.TextInput(attrs={"placeholder": "Ex. achat de 2 sacs d'aliment"})}
        labels = {"montant": "Montant prêté à chacun (F CFA)", "description": "Objet du prêt"}

    def clean(self):
        data = super().clean()
        if data.get("echeance") and data.get("date") and data["echeance"] < data["date"]:
            self.add_error("echeance", "L'échéance doit être après la date du prêt.")
        return data

    @transaction.atomic
    def save(self, commit=True):
        """Crée un prêt par producteur coché et renvoie la liste des prêts."""
        champs = {f: self.cleaned_data.get(f) for f in ("date", "montant", "taux_interet", "echeance", "description")}
        return [Pret.objects.create(producteur=p, type=Pret.TYPE_PRET, **champs)
                for p in self.cleaned_data["producteur"]]


class PretChoix(forms.ModelChoiceField):
    def label_from_instance(self, p):
        return (f"{p.producteur.nom} — prêt du {p.date:%d/%m/%Y} — reste {p.reste:,} F".replace(",", "\u202f"))


class RemboursementForm(forms.ModelForm):
    """Enregistrer un remboursement reçu, rattaché à un prêt."""

    pret_rembourse = PretChoix(queryset=Pret.objects.none(), label="Prêt remboursé")

    class Meta:
        model = Pret
        fields = ["pret_rembourse", "date", "montant", "description"]
        widgets = {"date": DATE, "montant": MONTANT,
                   "description": forms.TextInput(attrs={"placeholder": "Ex. remboursement en espèces"})}
        labels = {"montant": "Montant remboursé (F CFA)", "description": "Remarque"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ouverts = [p.pk for p in Pret.objects.filter(type=Pret.TYPE_PRET).prefetch_related("remboursements")
                   if p.reste > 0]
        self.fields["pret_rembourse"].queryset = (Pret.objects.filter(pk__in=ouverts)
                                                  .select_related("producteur").order_by("producteur__nom", "date"))

    def clean(self):
        data = super().clean()
        pret, montant = data.get("pret_rembourse"), data.get("montant")
        if pret and montant and montant > pret.reste:
            self.add_error("montant", f"Le reste à rembourser sur ce prêt est de {pret.reste:,} F.".replace(",", "\u202f"))
        return data

    def save(self, commit=True):
        self.instance.type = Pret.TYPE_REMBOURSEMENT
        self.instance.producteur = self.cleaned_data["pret_rembourse"].producteur
        return super().save(commit)


class CategorieChoix(forms.ModelChoiceField):
    """Liste des catégories regroupées : sorties (dépenses) puis entrées."""

    def __init__(self, **kwargs):
        super().__init__(queryset=CategorieCaisse.objects.filter(actif=True), **kwargs)

    def grouper(self):
        groupes = {"Sorties d'argent (dépenses)": [], "Entrées d'argent": []}
        for c in self.queryset:
            groupes["Entrées d'argent" if c.sens == CategorieCaisse.ENTREE else "Sorties d'argent (dépenses)"].append((c.pk, c.nom))
        self.choices = [("", "---------")] + [(k, v) for k, v in groupes.items() if v]


class OperationCaisseForm(forms.ModelForm):
    categorie = CategorieChoix(label="Catégorie")

    class Meta:
        model = OperationCaisse
        fields = ["date", "categorie", "libelle", "montant", "mode_paiement", "tiers", "piece"]
        widgets = {"date": DATE, "montant": MONTANT,
                   "libelle": forms.TextInput(attrs={"placeholder": "Ex. salaire du gardien – octobre"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].grouper()
