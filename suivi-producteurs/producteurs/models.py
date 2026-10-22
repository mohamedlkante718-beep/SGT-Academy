from datetime import timedelta

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Sum


class Secteur(models.Model):
    """Secteur d'activité (élevage, agriculture, maraîchage, pisciculture…), géré par l'administrateur."""

    nom = models.CharField(max_length=60, unique=True)
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """Produit proposé aux producteurs d'un secteur lors de la saisie (ex. Poulets adultes, Maïs)."""

    secteur = models.ForeignKey(Secteur, on_delete=models.CASCADE, related_name="produits")
    nom = models.CharField(max_length=80)
    unite = models.CharField("unité", max_length=30, blank=True, help_text="Ex. têtes, œufs, kg, sacs, hectares.")
    compter = models.BooleanField("se compte", default=True,
                                  help_text="Le producteur saisit une quantité (nombre, kg…).")
    valoriser = models.BooleanField("a une valeur", default=True,
                                    help_text="Le producteur saisit une valeur en F CFA.")
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["secteur__ordre", "ordre", "nom"]
        constraints = [models.UniqueConstraint(fields=["secteur", "nom"], name="produit_unique_par_secteur")]

    def __str__(self):
        return f"{self.nom} ({self.unite})" if self.unite else self.nom


class Responsable(models.Model):
    """Responsable de suivi : consulte et valide les fiches de ses producteurs, sans les modifier."""

    nom = models.CharField("nom et prénom", max_length=120)
    telephone = models.CharField("téléphone", max_length=20, unique=True,
                                 help_text="Sert d'identifiant de connexion.")
    actif = models.BooleanField(default=True)
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name="responsable", editable=False)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class Producteur(models.Model):
    nom = models.CharField("nom et prénom", max_length=120)
    telephone = models.CharField("téléphone", max_length=20, unique=True,
                                 help_text="Sert d'identifiant de connexion sur le téléphone.")
    produits = models.ManyToManyField(Produit, related_name="producteurs", blank=True,
                                      help_text="Les seuls produits que le producteur remplit sur son téléphone.")
    responsable = models.ForeignKey(Responsable, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="producteurs", help_text="Valide les fiches de ce producteur.")
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name="producteur", editable=False)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom

    def produits_attribues(self):
        return self.produits.filter(actif=True, secteur__actif=True).select_related("secteur")

    def secteurs(self):
        return Secteur.objects.filter(produits__producteurs=self).distinct()

    def fiche_precedente(self, semaine):
        return self.fiches.filter(semaine__lt=semaine).order_by("-semaine").first()

    def prets_en_cours(self, jusqu_au=None):
        qs = self.prets.all()
        if jusqu_au:
            qs = qs.filter(date__lte=jusqu_au)
        accordes = qs.filter(type=Pret.TYPE_PRET).aggregate(s=Sum("montant"))["s"] or 0
        rembourses = qs.filter(type=Pret.TYPE_REMBOURSEMENT).aggregate(s=Sum("montant"))["s"] or 0
        return accordes - rembourses


class Fiche(models.Model):
    """Situation hebdomadaire d'un producteur."""

    producteur = models.ForeignKey(Producteur, on_delete=models.CASCADE, related_name="fiches")
    semaine = models.DateField("semaine du")
    observations = models.TextField(blank=True)

    SOUMISE, VALIDEE, A_CORRIGER = "soumise", "validee", "a_corriger"
    STATUTS = [(SOUMISE, "À valider"), (VALIDEE, "Validée"), (A_CORRIGER, "À corriger")]
    statut = models.CharField(max_length=12, choices=STATUTS, default=SOUMISE)
    commentaire = models.TextField("commentaire du responsable", blank=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+", editable=False)
    valide_le = models.DateTimeField(null=True, blank=True, editable=False)
    saisie_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   blank=True, editable=False)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-semaine", "producteur__ordre"]
        constraints = [models.UniqueConstraint(fields=["producteur", "semaine"], name="une_fiche_par_semaine")]

    def __str__(self):
        return f"{self.producteur} — semaine du {self.semaine:%d/%m/%Y}"

    @property
    def fin(self):
        return self.semaine + timedelta(days=6)

    @property
    def total_valeurs(self):
        return sum(l.montant for l in self.valeurs.all())

    @property
    def total_depenses(self):
        return sum(d.montant for d in self.depenses.all())

    @property
    def total_ventes(self):
        return sum(v.montant for v in self.ventes.all())

    @property
    def resultat_net(self):
        return self.total_ventes - self.total_depenses


class LigneEffectif(models.Model):
    fiche = models.ForeignKey(Fiche, on_delete=models.CASCADE, related_name="effectifs")
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    libelle = models.CharField("élément", max_length=80)
    quantite = models.PositiveIntegerField("nombre")

    class Meta:
        ordering = ["id"]
        verbose_name = "effectif"

    def __str__(self):
        return f"{self.libelle} : {self.quantite}"


class LigneValeur(models.Model):
    fiche = models.ForeignKey(Fiche, on_delete=models.CASCADE, related_name="valeurs")
    produit = models.ForeignKey(Produit, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    libelle = models.CharField("élément", max_length=80)
    montant = models.PositiveIntegerField("valeur (F CFA)")

    class Meta:
        ordering = ["id"]
        verbose_name = "valeur"

    def __str__(self):
        return f"{self.libelle} : {self.montant} F"


MODES_PAIEMENT = [
    ("especes", "Espèces"),
    ("orange_money", "Orange Money"),
    ("moov_money", "Moov Money"),
    ("virement", "Virement"),
    ("autre", "Autre"),
]


class Depense(models.Model):
    CATEGORIES = [
        ("fournitures", "Fournitures + médicaments"),
        ("aliments", "Aliments"),
        ("autres", "Autres dépenses"),
    ]
    fiche = models.ForeignKey(Fiche, on_delete=models.CASCADE, related_name="depenses")
    date = models.DateField()
    categorie = models.CharField("catégorie", max_length=20, choices=CATEGORIES)
    description = models.CharField(max_length=200, blank=True)
    quantite = models.DecimalField("quantité", max_digits=10, decimal_places=2, null=True, blank=True)
    prix_unitaire = models.PositiveIntegerField("prix unitaire", null=True, blank=True)
    montant = models.PositiveIntegerField("montant (F CFA)")
    mode_paiement = models.CharField("paiement", max_length=20, choices=MODES_PAIEMENT, blank=True)

    class Meta:
        ordering = ["date", "id"]
        verbose_name = "dépense"


class Vente(models.Model):
    fiche = models.ForeignKey(Fiche, on_delete=models.CASCADE, related_name="ventes")
    date = models.DateField()
    categorie = models.CharField("catégorie / lot", max_length=80)
    description = models.CharField(max_length=200, blank=True)
    poids = models.CharField("poids (kg / g)", max_length=30, blank=True)
    quantite = models.DecimalField("quantité", max_digits=10, decimal_places=2, null=True, blank=True)
    prix_unitaire = models.PositiveIntegerField("prix unitaire", null=True, blank=True)
    montant = models.PositiveIntegerField("montant (F CFA)")
    mode_paiement = models.CharField("paiement", max_length=20, choices=MODES_PAIEMENT, blank=True)
    client = models.CharField("client / remarque", max_length=120, blank=True)

    class Meta:
        ordering = ["date", "id"]


class Pret(models.Model):
    """Prêt ou avance accordé par le CIAF/CE, ou remboursement reçu. Saisi par l'administrateur."""

    TYPE_PRET = "pret"
    TYPE_REMBOURSEMENT = "remboursement"
    TYPES = [(TYPE_PRET, "Prêt / avance accordé"), (TYPE_REMBOURSEMENT, "Remboursement reçu")]

    producteur = models.ForeignKey(Producteur, on_delete=models.CASCADE, related_name="prets")
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TYPES, default=TYPE_PRET)
    montant = models.PositiveIntegerField("montant (F CFA)")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "prêt / remboursement"
        verbose_name_plural = "prêts et remboursements"


class Parametres(models.Model):
    """Réglages modifiables depuis l'administration (une seule ligne) : le logo de la structure."""

    logo = models.FileField(
        upload_to="logo/", blank=True,
        validators=[FileExtensionValidator(["png", "jpg", "jpeg", "webp", "svg"])],
        help_text="Image PNG ou JPG, de préférence carrée ou en largeur, fond transparent si possible. "
                  "Elle s'affiche en haut des pages, sur la page de connexion et dans les rapports.")

    class Meta:
        verbose_name = "logo"
        verbose_name_plural = "logo"

    def __str__(self):
        return "Logo de la structure"
