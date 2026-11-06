from datetime import date, timedelta
from decimal import Decimal

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
        """Reste dû par le producteur : capital + intérêts des prêts, moins les remboursements."""
        qs = self.prets.all()
        if jusqu_au:
            qs = qs.filter(date__lte=jusqu_au)
        du = sum(p.total_du for p in qs.filter(type=Pret.TYPE_PRET))
        rembourses = qs.filter(type=Pret.TYPE_REMBOURSEMENT).aggregate(s=Sum("montant"))["s"] or 0
        return du - rembourses


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
    # Pour un prêt :
    taux_interet = models.DecimalField("taux d'intérêt (%)", max_digits=5, decimal_places=2, default=0,
                                       help_text="Pourcentage ajouté au montant prêté. 0 si le prêt est sans intérêt.")
    echeance = models.DateField("date d'échéance", null=True, blank=True,
                                help_text="Date à laquelle le prêt doit être entièrement remboursé.")
    # Pour un remboursement : le prêt qu'il rembourse.
    pret_rembourse = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True,
                                       related_name="remboursements", verbose_name="prêt remboursé",
                                       limit_choices_to={"type": TYPE_PRET})

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "prêt / remboursement"
        verbose_name_plural = "prêts et remboursements"

    def __str__(self):
        return f"{self.producteur} — {self.montant:,} F du {self.date:%d/%m/%Y}".replace(",", "\u202f")

    @property
    def interets(self):
        return int((Decimal(self.montant) * self.taux_interet / 100).quantize(Decimal("1"))) if self.type == self.TYPE_PRET else 0

    @property
    def total_du(self):
        return self.montant + self.interets

    @property
    def rembourse(self):
        return sum(r.montant for r in self.remboursements.all())

    @property
    def reste(self):
        return max(self.total_du - self.rembourse, 0)

    @property
    def pct_rembourse(self):
        return round(min(self.rembourse / self.total_du * 100, 100), 1) if self.total_du else 0

    @property
    def statut(self):
        if self.reste == 0:
            return "rembourse"
        if self.echeance and self.echeance < date.today():
            return "retard"
        return "en_cours"


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


# ---------------------------------------------------------------- caisse du centre

class CategorieCaisse(models.Model):
    """Rubrique d'entrée ou de sortie d'argent du centre (salaires, cuisine, électricité…)."""

    ENTREE, SORTIE = "entree", "sortie"
    SENS = [(ENTREE, "Entrée d'argent"), (SORTIE, "Sortie d'argent (dépense)")]

    nom = models.CharField(max_length=80)
    sens = models.CharField(max_length=10, choices=SENS, default=SORTIE)
    ordre = models.PositiveIntegerField("ordre d'affichage", default=0)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ["sens", "ordre", "nom"]
        verbose_name = "catégorie de caisse"
        verbose_name_plural = "catégories de caisse"
        constraints = [models.UniqueConstraint(fields=["nom", "sens"], name="categorie_caisse_unique")]

    def __str__(self):
        return self.nom


class OperationCaisse(models.Model):
    """Une entrée ou une sortie d'argent du centre : salaire, repas, facture d'électricité, subvention…"""

    date = models.DateField()
    categorie = models.ForeignKey(CategorieCaisse, on_delete=models.PROTECT, related_name="operations",
                                  verbose_name="catégorie")
    libelle = models.CharField("description", max_length=200)
    montant = models.PositiveIntegerField("montant (F CFA)")
    mode_paiement = models.CharField("paiement", max_length=20, choices=MODES_PAIEMENT, blank=True)
    tiers = models.CharField("payé à / reçu de", max_length=120, blank=True,
                             help_text="Ex. nom de l'employé, du fournisseur, du donateur.")
    piece = models.FileField("pièce justificative", upload_to="pieces/%Y/%m/", blank=True,
                             validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg", "webp"])],
                             help_text="Photo du reçu ou de la facture (facultatif).")
    saisie_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   editable=False)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "opération de caisse"
        verbose_name_plural = "caisse du centre"

    def __str__(self):
        return f"{self.date:%d/%m/%Y} — {self.libelle} — {self.montant} F"

    @property
    def est_entree(self):
        return self.categorie.sens == CategorieCaisse.ENTREE


class TentativeConnexion(models.Model):
    """Journal des connexions : sert à bloquer les essais répétés de codes PIN (piratage) et à voir
    qui s'est connecté, quand et depuis quelle adresse."""

    identifiant = models.CharField(max_length=150, db_index=True)
    ip = models.GenericIPAddressField("adresse IP", null=True, blank=True)
    reussie = models.BooleanField("réussie", default=False)
    quand = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-quand"]
        verbose_name = "connexion"
        verbose_name_plural = "journal des connexions"

    def __str__(self):
        return f"{self.identifiant} — {'réussie' if self.reussie else 'refusée'}"


# ---------------------------------------------------------------- paiement mensuel des producteurs

GROUPE_COMPTABLE, GROUPE_PROMOTEUR = "Comptable", "Promoteur"


def _dans_groupe(user, groupe):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name=groupe).exists())


def peut_preparer_paiements(user):
    """Le comptable (ou le super-administrateur) choisit les producteurs et les montants du mois."""
    return _dans_groupe(user, GROUPE_COMPTABLE)


def peut_valider_paiements(user):
    """Le promoteur (ou le super-administrateur) valide ou refuse le paiement du mois."""
    return _dans_groupe(user, GROUPE_PROMOTEUR)


class PaiementMensuel(models.Model):
    """Paiement d'un mois : préparé par le comptable, validé par le promoteur, puis payé (sortie de caisse)."""

    BROUILLON, A_VALIDER, VALIDE, REFUSE, PAYE = "brouillon", "a_valider", "valide", "refuse", "paye"
    STATUTS = [(BROUILLON, "En préparation"), (A_VALIDER, "À valider par le promoteur"), (VALIDE, "Validé, à payer"),
               (REFUSE, "Refusé, à revoir"), (PAYE, "Payé")]

    mois = models.DateField("mois", unique=True, help_text="Premier jour du mois payé.")
    statut = models.CharField(max_length=12, choices=STATUTS, default=BROUILLON)
    prepare_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="+", verbose_name="préparé par")
    envoye_le = models.DateTimeField("envoyé pour validation le", null=True, blank=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="+", verbose_name="validé ou refusé par")
    valide_le = models.DateTimeField("validé ou refusé le", null=True, blank=True)
    commentaire = models.TextField("commentaire du promoteur", blank=True)
    paye_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="+", verbose_name="payé par")
    date_paiement = models.DateField("payé le", null=True, blank=True)
    mode_paiement = models.CharField("paiement", max_length=20, choices=MODES_PAIEMENT, blank=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-mois"]
        verbose_name = "paiement mensuel"
        verbose_name_plural = "paiements mensuels"

    def __str__(self):
        from .services import MOIS_NOMS
        return f"Paiement de {MOIS_NOMS[self.mois.month - 1]} {self.mois.year}"

    @property
    def total(self):
        return sum(l.montant for l in self.lignes.all())

    @property
    def modifiable(self):
        return self.statut in (self.BROUILLON, self.REFUSE)


class LignePaiement(models.Model):
    paiement = models.ForeignKey(PaiementMensuel, on_delete=models.CASCADE, related_name="lignes")
    producteur = models.ForeignKey(Producteur, on_delete=models.PROTECT, related_name="paiements")
    montant = models.PositiveIntegerField("montant (F CFA)")
    motif = models.CharField(max_length=150, blank=True)
    operation = models.OneToOneField(OperationCaisse, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="ligne_paiement", editable=False)

    class Meta:
        ordering = ["producteur__ordre", "producteur__nom"]
        constraints = [models.UniqueConstraint(fields=["paiement", "producteur"], name="un_paiement_par_producteur")]

    def __str__(self):
        return f"{self.producteur} — {self.montant} F"
