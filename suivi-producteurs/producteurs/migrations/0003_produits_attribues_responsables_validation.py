# Produits attribués à chaque producteur, responsables de suivi, validation des fiches.

import unicodedata

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


QUANTITE_SEULEMENT = {"Ovins", "Caprins", "Lapines"}
VALEUR_SEULEMENT = {"Ovins & caprins"}


def cle(libelle):
    s = unicodedata.normalize("NFD", libelle or "").encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def convertir(apps, schema_editor):
    Secteur = apps.get_model("producteurs", "Secteur")
    Produit = apps.get_model("producteurs", "Produit")
    Producteur = apps.get_model("producteurs", "Producteur")
    Fiche = apps.get_model("producteurs", "Fiche")
    LigneEffectif = apps.get_model("producteurs", "LigneEffectif")
    LigneValeur = apps.get_model("producteurs", "LigneValeur")

    Secteur.objects.get_or_create(nom="Pépinière", defaults={"ordre": 3})

    # Ce qui se compte (nombre) et ce qui a une valeur en F CFA, d'après la fiche Excel.
    for p in Produit.objects.all():
        if p.nom in VALEUR_SEULEMENT:
            p.compter = False
        elif p.nom in QUANTITE_SEULEMENT or p.nom.startswith(("Œufs", "Mortalités")):
            p.valoriser = False
        p.save()

    # Chaque producteur reçoit les produits qui figurent sur ses fiches, rattachés aux lignes existantes.
    for producteur in Producteur.objects.all():
        catalogue = {cle(p.nom): p for p in Produit.objects.filter(secteur__in=producteur.secteurs.all())}
        for modele in (LigneEffectif, LigneValeur):
            for ligne in modele.objects.filter(fiche__producteur=producteur, produit__isnull=True):
                produit = catalogue.get(cle(ligne.libelle))
                if produit:
                    ligne.produit = produit
                    ligne.save(update_fields=["produit"])
                    producteur.produits.add(produit)

    # Les fiches déjà enregistrées (reprise de l'Excel) sont considérées comme validées.
    Fiche.objects.update(statut="validee")


class Migration(migrations.Migration):

    dependencies = [
        ("producteurs", "0002_secteurs_produits"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="fiche",
            name="commentaire",
            field=models.TextField(
                blank=True, verbose_name="commentaire du responsable"
            ),
        ),
        migrations.AddField(
            model_name="fiche",
            name="statut",
            field=models.CharField(
                choices=[
                    ("soumise", "À valider"),
                    ("validee", "Validée"),
                    ("a_corriger", "À corriger"),
                ],
                default="soumise",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="fiche",
            name="valide_le",
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="fiche",
            name="valide_par",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="ligneeffectif",
            name="produit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="producteurs.produit",
            ),
        ),
        migrations.AddField(
            model_name="lignevaleur",
            name="produit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="producteurs.produit",
            ),
        ),
        migrations.AddField(
            model_name="producteur",
            name="produits",
            field=models.ManyToManyField(
                blank=True,
                help_text="Les seuls produits que le producteur remplit sur son téléphone.",
                related_name="producteurs",
                to="producteurs.produit",
            ),
        ),
        migrations.AddField(
            model_name="produit",
            name="compter",
            field=models.BooleanField(
                default=True,
                help_text="Le producteur saisit une quantité (nombre, kg…).",
                verbose_name="se compte",
            ),
        ),
        migrations.AddField(
            model_name="produit",
            name="valoriser",
            field=models.BooleanField(
                default=True,
                help_text="Le producteur saisit une valeur en F CFA.",
                verbose_name="a une valeur",
            ),
        ),
        migrations.CreateModel(
            name="Responsable",
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
                ("nom", models.CharField(max_length=120, verbose_name="nom et prénom")),
                (
                    "telephone",
                    models.CharField(
                        help_text="Sert d'identifiant de connexion.",
                        max_length=20,
                        unique=True,
                        verbose_name="téléphone",
                    ),
                ),
                ("actif", models.BooleanField(default=True)),
                (
                    "utilisateur",
                    models.OneToOneField(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="responsable",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["nom"],
            },
        ),
        migrations.AddField(
            model_name="producteur",
            name="responsable",
            field=models.ForeignKey(
                blank=True,
                help_text="Valide les fiches de ce producteur.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="producteurs",
                to="producteurs.responsable",
            ),
        ),
        migrations.RunPython(convertir, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="producteur",
            name="secteurs",
        ),
    ]
