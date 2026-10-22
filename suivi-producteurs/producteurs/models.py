from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Sum


class Producteur(models.Model):
    VOLET_ELEVAGE = "elevage"
    VOLET_AGRICULTURE = "agriculture"
    VOLETS = [(VOLET_ELEVAGE, "Élevage"), (VOLET_AGRICULTURE, "Agriculture")]

    nom = models.CharField("nom et prénom", max_length=120)
    telephone = models.CharField("téléphone", max_length=20, unique=True,
                                 help_text="Sert d'identifiant de connexion sur le téléphone.")
    volet = models.CharField(max_length=20, choices=VOLETS, default=VOLET_ELEVAGE)
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name="producteur", editable=False)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ordre", "nom"]

    def __str__(self):
        return self.nom

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
    libelle = models.CharField("élément", max_length=80)
    quantite = models.PositiveIntegerField("nombre")

    class Meta:
        ordering = ["id"]
        verbose_name = "effectif"

    def __str__(self):
        return f"{self.libelle} : {self.quantite}"


class LigneValeur(models.Model):
    fiche = models.ForeignKey(Fiche, on_delete=models.CASCADE, related_name="valeurs")
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
    """Prêt ou avance accordé par le CIAF, ou remboursement reçu. Saisi par l'administrateur."""

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
