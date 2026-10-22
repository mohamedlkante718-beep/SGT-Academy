from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

from .models import Producteur, Produit, Responsable


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

    def clean_username(self):
        brut = self.cleaned_data["username"].strip()
        # Les administrateurs se connectent avec leur nom d'utilisateur, les autres avec leur numéro.
        tel = normaliser_telephone(brut)
        return tel if tel and len(tel) >= 6 and tel.lstrip("+").isdigit() else brut


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
    produits = ProduitsParSecteur(required=False, label="Produits attribués",
                                  help_text="Le producteur ne remplira que ces produits sur son téléphone.")

    class Meta:
        model = Producteur
        fields = ["nom", "telephone", "responsable", "produits", "actif", "ordre"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produits"].grouper()


class ResponsableAdminForm(CompteTelephoneForm):
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


class ValidationForm(forms.Form):
    decision = forms.ChoiceField(choices=[("valider", "Valider"), ("corriger", "Demander une correction")])
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={
        "rows": 2, "placeholder": "Ce qu'il faut corriger (obligatoire pour une demande de correction)"}))

    def clean(self):
        data = super().clean()
        if data.get("decision") == "corriger" and not data.get("commentaire", "").strip():
            self.add_error("commentaire", "Expliquez au producteur ce qu'il doit corriger.")
        return data
