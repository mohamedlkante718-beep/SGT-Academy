from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory

from django.contrib.auth import get_user_model

from .models import Fiche, LigneEffectif, LigneValeur, Producteur


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
        "inactive": "Ce compte est désactivé. Contactez l'administrateur du CIAF.",
    }

    def clean_username(self):
        brut = self.cleaned_data["username"].strip()
        # Les administrateurs se connectent avec leur nom d'utilisateur, les producteurs avec leur numéro.
        tel = normaliser_telephone(brut)
        return tel if tel and len(tel) >= 6 and tel.lstrip("+").isdigit() else brut


class ProducteurAdminForm(forms.ModelForm):
    code_pin = forms.CharField(
        label="Code PIN", required=False, min_length=4, max_length=6,
        help_text="4 à 6 chiffres, à communiquer au producteur. Laissez vide pour garder le code actuel.",
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
    )

    class Meta:
        model = Producteur
        fields = ["nom", "telephone", "secteurs", "actif", "ordre"]
        widgets = {"secteurs": forms.CheckboxSelectMultiple}

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
            self.add_error("code_pin", "Choisissez un code PIN pour que ce producteur puisse se connecter.")
        return data


class FicheForm(forms.ModelForm):
    class Meta:
        model = Fiche
        fields = ["observations"]
        widgets = {"observations": forms.Textarea(attrs={
            "rows": 3, "placeholder": "État des animaux, naissances, maladies, mortalités…"})}


def formsets(extra_effectifs=0, extra_valeurs=0):
    """Jeux de formulaires de la saisie mobile : le producteur ne renseigne que ses produits."""
    return {
        "effectifs": inlineformset_factory(
            Fiche, LigneEffectif, fields=["libelle", "quantite"], extra=extra_effectifs, can_delete=True,
            widgets={"quantite": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0})}),
        "valeurs": inlineformset_factory(
            Fiche, LigneValeur, fields=["libelle", "montant"], extra=extra_valeurs, can_delete=True,
            widgets={"montant": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0})}),
    }
