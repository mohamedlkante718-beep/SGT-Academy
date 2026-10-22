from datetime import date

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Depense, Fiche, LigneEffectif, LigneValeur, Pret, Producteur
from .services import debut_semaine, evolution

S1 = date(2026, 10, 14)
S2 = date(2026, 10, 21)


def creer_producteur(nom, tel, pin="1234"):
    user = get_user_model().objects.create_user(username=tel, password=pin)
    return Producteur.objects.create(nom=nom, telephone=tel, utilisateur=user)


class CalculsTests(TestCase):
    def test_debut_semaine_mercredi(self):
        self.assertEqual(debut_semaine(date(2026, 10, 20)), S1)  # mardi → mercredi précédent
        self.assertEqual(debut_semaine(date(2026, 10, 21)), S2)

    def test_evolution(self):
        self.assertEqual(evolution(None, 10)["etat"], "nouveau")
        self.assertEqual(evolution(100, 150)["etat"], "hausse")
        self.assertEqual(evolution(100, 150)["pct"], 50.0)
        self.assertEqual(evolution(100, 80)["etat"], "baisse")
        self.assertEqual(evolution(5, 5)["etat"], "stable")
        # Mortalités : une hausse est une mauvaise nouvelle.
        self.assertEqual(evolution(3, 6, inverse=True)["etat"], "baisse")

    def test_chargement_initial(self):
        call_command("charger_semaine_initiale", verbosity=0)
        self.assertEqual(Producteur.objects.count(), 12)
        total = sum(f.total_valeurs for f in Fiche.objects.filter(semaine=S1))
        self.assertEqual(total, 6_430_000)
        call_command("charger_semaine_initiale", verbosity=0)  # relancer ne crée pas de doublon
        self.assertEqual(Fiche.objects.count(), 12)


class SaisieMobileTests(TestCase):
    def setUp(self):
        self.p = creer_producteur("Alpha GANO", "76000001")
        self.autre = creer_producteur("Mariam KONE", "76000002")
        f = Fiche.objects.create(producteur=self.p, semaine=S1)
        LigneEffectif.objects.create(fiche=f, libelle="Poulets", quantite=45)
        LigneValeur.objects.create(fiche=f, libelle="Poulets", montant=270000)

    def test_connexion_par_telephone_avec_espaces(self):
        r = self.client.post(reverse("connexion"), {"username": "76 00 00 01", "password": "1234"})
        self.assertRedirects(r, reverse("accueil"))

    def test_producteur_ne_voit_pas_le_tableau_de_bord(self):
        self.client.login(username="76000001", password="1234")
        r = self.client.get(reverse("tableau"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    def test_nouvelle_fiche_reprend_les_elements_precedents(self):
        self.client.login(username="76000001", password="1234")
        r = self.client.get(reverse("saisie_semaine", args=["2026-10-21"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'value="Poulets"', count=2)
        self.assertContains(r, "270 000 F")  # valeur de la semaine d'avant rappelée

    def test_enregistrer_fiche_produits(self):
        self.client.login(username="76000001", password="1234")
        data = {
            "observations": "RAS",
            "effectifs-TOTAL_FORMS": "1", "effectifs-INITIAL_FORMS": "0",
            "effectifs-0-libelle": "Poulets", "effectifs-0-quantite": "50",
            "valeurs-TOTAL_FORMS": "1", "valeurs-INITIAL_FORMS": "0",
            "valeurs-0-libelle": "Poulets", "valeurs-0-montant": "300000",
        }
        r = self.client.post(reverse("saisie_semaine", args=["2026-10-21"]), data)
        self.assertRedirects(r, reverse("accueil"))
        f = Fiche.objects.get(producteur=self.p, semaine=S2)
        self.assertEqual(f.total_valeurs, 300000)
        self.assertEqual(f.saisie_par.username, "76000001")
        # La fiche est rattachée au producteur connecté, jamais à un autre.
        self.assertFalse(Fiche.objects.filter(producteur=self.autre).exists())

    def test_formulaire_mobile_sans_finances(self):
        self.client.login(username="76000001", password="1234")
        r = self.client.get(reverse("saisie_semaine", args=["2026-10-21"]))
        self.assertNotContains(r, "depenses-TOTAL_FORMS")
        self.assertNotContains(r, "ventes-TOTAL_FORMS")


@override_settings(STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class GestionTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("chef", password="secret-123")
        self.p = creer_producteur("Alpha GANO", "76000001")
        for s, montant in ((S1, 100000), (S2, 150000)):
            f = Fiche.objects.create(producteur=self.p, semaine=s)
            LigneValeur.objects.create(fiche=f, libelle="Poulets", montant=montant)
        f2 = Fiche.objects.get(semaine=S2)
        Depense.objects.create(fiche=f2, date=S2, categorie="aliments", montant=20000)
        Pret.objects.create(producteur=self.p, date=S2, montant=50000)
        Pret.objects.create(producteur=self.p, date=S2, type=Pret.TYPE_REMBOURSEMENT, montant=10000)
        self.client.login(username="chef", password="secret-123")

    def test_tableau_montre_evolution_et_bilan(self):
        r = self.client.get(reverse("tableau"))
        self.assertEqual(r.status_code, 200)
        ligne = r.context["lignes"][0]
        self.assertEqual((ligne["precedent"], ligne["actuel"]), (100000, 150000))
        self.assertEqual(ligne["evo"]["etat"], "hausse")
        self.assertEqual(ligne["resultat"], -20000)
        self.assertEqual(ligne["prets"], 40000)
        self.assertContains(r, "▲ +50 000 F")

    def test_export_csv(self):
        r = self.client.get(reverse("tableau") + "?format=csv")
        self.assertEqual(r["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Alpha GANO;100000;150000;50000;20000;0;-20000;40000", r.content.decode("utf-8-sig"))

    def test_fiche_producteur(self):
        r = self.client.get(reverse("fiche_producteur", args=[self.p.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Prêts et remboursements")

    def test_admin_cree_producteur_avec_pin(self):
        r = self.client.post(reverse("admin:producteurs_producteur_add"), {
            "nom": "Siaka KEITA", "volet": "elevage", "actif": "on", "ordre": "3",
            "telephone": "+223 66 00 00 03", "code_pin": "4321",
            "prets-TOTAL_FORMS": "0", "prets-INITIAL_FORMS": "0",
        })
        self.assertEqual(r.status_code, 302)
        p = Producteur.objects.get(nom="Siaka KEITA")
        self.assertEqual(p.telephone, "+22366000003")
        self.client.logout()
        self.assertTrue(self.client.login(username="+22366000003", password="4321"))
