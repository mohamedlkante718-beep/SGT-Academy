# Caisse du centre et prêts avec intérêts et échéance. Généré le 2026-10-24 11:36

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


SORTIES = [
    "Salaires et indemnités", "Alimentation / cuisine", "Électricité", "Eau",
    "Réparations et entretien", "Transport et carburant", "Fournitures et petit matériel",
    "Communication (crédit, internet)", "Intrants agricoles et vétérinaires",
    "Frais bancaires et Mobile Money", "Autres dépenses de fonctionnement",
]
ENTREES = [
    "Apport du promoteur", "Subventions et dons", "Ventes du centre",
    "Frais de formation / cotisations", "Autres recettes",
]


def initialiser(apps, schema_editor):
    Categorie = apps.get_model("producteurs", "CategorieCaisse")
    for sens, noms in (("sortie", SORTIES), ("entree", ENTREES)):
        for i, nom in enumerate(noms, start=1):
            Categorie.objects.get_or_create(nom=nom, sens=sens, defaults={"ordre": i})
    # Les remboursements déjà saisis sont rattachés au plus ancien prêt du producteur.
    Pret = apps.get_model("producteurs", "Pret")
    for r in Pret.objects.filter(type="remboursement", pret_rembourse__isnull=True):
        pret = Pret.objects.filter(type="pret", producteur_id=r.producteur_id, date__lte=r.date).order_by("date").first()
        if pret:
            r.pret_rembourse = pret
            r.save(update_fields=["pret_rembourse"])


class Migration(migrations.Migration):

    dependencies = [
        ("producteurs", "0004_logo"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="pret",
            name="echeance",
            field=models.DateField(
                blank=True,
                help_text="Date à laquelle le prêt doit être entièrement remboursé.",
                null=True,
                verbose_name="date d'échéance",
            ),
        ),
        migrations.AddField(
            model_name="pret",
            name="pret_rembourse",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"type": "pret"},
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="remboursements",
                to="producteurs.pret",
                verbose_name="prêt remboursé",
            ),
        ),
        migrations.AddField(
            model_name="pret",
            name="taux_interet",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Pourcentage ajouté au montant prêté. 0 si le prêt est sans intérêt.",
                max_digits=5,
                verbose_name="taux d'intérêt (%)",
            ),
        ),
        migrations.CreateModel(
            name="CategorieCaisse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=80)),
                (
                    "sens",
                    models.CharField(
                        choices=[
                            ("entree", "Entrée d'argent"),
                            ("sortie", "Sortie d'argent (dépense)"),
                        ],
                        default="sortie",
                        max_length=10,
                    ),
                ),
                (
                    "ordre",
                    models.PositiveIntegerField(
                        default=0, verbose_name="ordre d'affichage"
                    ),
                ),
                ("actif", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "catégorie de caisse",
                "verbose_name_plural": "catégories de caisse",
                "ordering": ["sens", "ordre", "nom"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("nom", "sens"), name="categorie_caisse_unique"
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="OperationCaisse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField()),
                (
                    "libelle",
                    models.CharField(max_length=200, verbose_name="description"),
                ),
                (
                    "montant",
                    models.PositiveIntegerField(verbose_name="montant (F CFA)"),
                ),
                (
                    "mode_paiement",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("especes", "Espèces"),
                            ("orange_money", "Orange Money"),
                            ("moov_money", "Moov Money"),
                            ("virement", "Virement"),
                            ("autre", "Autre"),
                        ],
                        max_length=20,
                        verbose_name="paiement",
                    ),
                ),
                (
                    "tiers",
                    models.CharField(
                        blank=True,
                        help_text="Ex. nom de l'employé, du fournisseur, du donateur.",
                        max_length=120,
                        verbose_name="payé à / reçu de",
                    ),
                ),
                (
                    "piece",
                    models.FileField(
                        blank=True,
                        help_text="Photo du reçu ou de la facture (facultatif).",
                        upload_to="pieces/%Y/%m/",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                ["pdf", "png", "jpg", "jpeg", "webp"]
                            )
                        ],
                        verbose_name="pièce justificative",
                    ),
                ),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                (
                    "categorie",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="operations",
                        to="producteurs.categoriecaisse",
                        verbose_name="catégorie",
                    ),
                ),
                (
                    "saisie_par",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "opération de caisse",
                "verbose_name_plural": "caisse du centre",
                "ordering": ["-date", "-id"],
            },
        ),
        migrations.RunPython(initialiser, migrations.RunPython.noop),
    ]
