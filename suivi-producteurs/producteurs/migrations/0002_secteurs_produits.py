# Remplace le choix figé « volet » par des secteurs et des produits gérés par l'administrateur.

import django.db.models.deletion
from django.db import migrations, models


ELEVAGE = [
    # (produit, unité) repris de la fiche Excel CIAF du 14 au 20 octobre 2026
    ("Taureau", "têtes"), ("Ovins", "têtes"), ("Caprins", "têtes"), ("Ovins & caprins", "têtes"),
    ("Poulets", "têtes"), ("Poulets adultes", "têtes"), ("Poulets adultes moyens", "têtes"), ("Poulets moyens", "têtes"),
    ("Pintades", "têtes"), ("Pintadeaux", "têtes"), ("Pintadeaux adultes moyens", "têtes"),
    ("Dindes", "têtes"), ("Dindonneaux", "têtes"), ("Canards", "têtes"), ("Oies", "têtes"),
    ("Cailles adultes", "têtes"), ("Cailleteaux", "têtes"), ("Lapins", "têtes"), ("Lapines", "têtes"),
    ("Œufs couvés", "œufs"), ("Œufs poules couvés", "œufs"), ("Œufs pintades couvés", "œufs"),
    ("Œufs dinde couvés", "œufs"), ("Œufs couvés canard", "œufs"), ("Œufs disponibles", "œufs"),
    ("Mortalités poulets", "têtes"), ("Mortalités pintadeaux", "têtes"), ("Mortalités cailleteaux", "têtes"),
]


def creer_secteurs(apps, schema_editor):
    Secteur = apps.get_model("producteurs", "Secteur")
    Produit = apps.get_model("producteurs", "Produit")
    Producteur = apps.get_model("producteurs", "Producteur")
    elevage, _ = Secteur.objects.get_or_create(nom="Élevage", defaults={"ordre": 1})
    # Agriculture : produits à compléter avec la fiche de suivi de M. Traoré.
    agriculture, _ = Secteur.objects.get_or_create(nom="Agriculture", defaults={"ordre": 2})
    for i, (nom, unite) in enumerate(ELEVAGE, start=1):
        Produit.objects.get_or_create(secteur=elevage, nom=nom, defaults={"unite": unite, "ordre": i})
    for p in Producteur.objects.all():
        p.secteurs.add(agriculture if p.volet == "agriculture" else elevage)


class Migration(migrations.Migration):

    dependencies = [
        ("producteurs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Secteur",
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
                ("nom", models.CharField(max_length=60, unique=True)),
                (
                    "ordre",
                    models.PositiveIntegerField(
                        default=0, verbose_name="ordre d'affichage"
                    ),
                ),
                ("actif", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["ordre", "nom"],
            },
        ),
        migrations.AddField(
            model_name="producteur",
            name="secteurs",
            field=models.ManyToManyField(
                blank=True,
                help_text="Le producteur verra les produits de ces secteurs sur son téléphone.",
                related_name="producteurs",
                to="producteurs.secteur",
            ),
        ),
        migrations.CreateModel(
            name="Produit",
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
                    "unite",
                    models.CharField(
                        blank=True,
                        help_text="Ex. têtes, œufs, kg, sacs, hectares.",
                        max_length=30,
                        verbose_name="unité",
                    ),
                ),
                (
                    "ordre",
                    models.PositiveIntegerField(
                        default=0, verbose_name="ordre d'affichage"
                    ),
                ),
                ("actif", models.BooleanField(default=True)),
                (
                    "secteur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="produits",
                        to="producteurs.secteur",
                    ),
                ),
            ],
            options={
                "ordering": ["secteur__ordre", "ordre", "nom"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("secteur", "nom"), name="produit_unique_par_secteur"
                    )
                ],
            },
        ),
        migrations.RunPython(creer_secteurs, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="producteur",
            name="volet",
        ),
    ]
