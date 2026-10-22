from datetime import date

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Depense, Fiche, LigneEffectif, LigneValeur, Pret, Producteur, Produit, Responsable, Secteur
from .services import debut_semaine, evolution

S1 = date(2026, 10, 14)
S2 = date(2026, 10, 21)
SAISIE_S2 = reverse("saisie_semaine", args=["2026-10-21"])


def compte(username, pin="1234"):
    return get_user_model().objects.create_user(username=username, password=pin)


def creer_producteur(nom, tel, produits=()):
    p = Producteur.objects.create(nom=nom, telephone=tel, utilisateur=compte(tel))
    p.produits.set(produits)
    return p


def produit(nom):
    return Produit.objects.get(secteur__nom="Élevage", nom=nom)


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
        self.assertEqual(evolution(3, 6, inverse=True)["etat"], "baisse")  # mortalités

    def test_secteurs_crees_par_les_migrations(self):
        self.assertEqual(list(Secteur.objects.values_list("nom", flat=True)), ["Élevage", "Agriculture", "Pépinière"])
        self.assertFalse(produit("Mortalités cailleteaux").valoriser)
        self.assertFalse(produit("Ovins & caprins").compter)

    def test_chargement_des_fiches_excel(self):
        call_command("charger_fiches_excel", verbosity=0)
        self.assertEqual(Producteur.objects.count(), 12)
        totaux = {s: sum(f.total_valeurs for f in Fiche.objects.filter(semaine=s))
                  for s in (date(2026, 10, 1), date(2026, 10, 8), S1)}
        self.assertEqual(totaux, {date(2026, 10, 1): 6_289_600, date(2026, 10, 8): 6_152_600, S1: 6_430_000})
        self.assertEqual(sum(d.montant for d in Depense.objects.all()), 278_000 + 150_000)
        alpha = Producteur.objects.get(nom="Alpha GANO")
        self.assertIn(produit("Nouvelles éclosions pintadeaux"), alpha.produits.all())
        self.assertFalse(produit("Nouvelles éclosions pintadeaux").valoriser)
        self.assertFalse(Fiche.objects.exclude(statut=Fiche.VALIDEE).exists())
        self.assertEqual(Fiche.objects.count(), 34)  # Thara KANOUTE n'a de fiche que pour la 3e semaine
        call_command("charger_fiches_excel", verbosity=0)  # relancer ne crée pas de doublon
        self.assertEqual(Fiche.objects.count(), 34)


class SaisieMobileTests(TestCase):
    def setUp(self):
        self.poulets, self.mort = produit("Poulets"), produit("Mortalités pintadeaux")
        self.p = creer_producteur("Alpha GANO", "76000001", [self.poulets, self.mort])
        self.autre = creer_producteur("Mariam KONE", "76000002")
        f = Fiche.objects.create(producteur=self.p, semaine=S1, statut=Fiche.VALIDEE)
        LigneEffectif.objects.create(fiche=f, produit=self.poulets, libelle="Poulets", quantite=45)
        LigneValeur.objects.create(fiche=f, produit=self.poulets, libelle="Poulets", montant=270000)
        self.client.login(username="76000001", password="1234")

    def test_connexion_par_telephone_avec_espaces(self):
        self.client.logout()
        self.assertContains(self.client.get(reverse("connexion")), "Centre d&#x27;Incubation Agroforestière Champ École")
        r = self.client.post(reverse("connexion"), {"username": "76 00 00 01", "password": "1234"})
        self.assertRedirects(r, reverse("accueil"))

    def test_producteur_ne_voit_pas_le_tableau_de_bord(self):
        self.assertRedirects(self.client.get(reverse("tableau")), reverse("accueil"))

    def test_seuls_les_produits_attribues(self):
        r = self.client.get(SAISIE_S2)
        self.assertContains(r, 'name="q_%d"' % self.poulets.pk)
        self.assertContains(r, 'name="v_%d"' % self.poulets.pk)
        self.assertContains(r, 'name="q_%d"' % self.mort.pk)
        self.assertNotContains(r, 'name="v_%d"' % self.mort.pk)  # une mortalité n'a pas de valeur
        self.assertNotContains(r, "Taureau")
        self.assertContains(r, "270 000 F")  # rappel de la semaine d'avant
        self.assertNotContains(r, "Dépenses")

    def test_envoyer_fiche(self):
        r = self.client.post(SAISIE_S2, {f"q_{self.poulets.pk}": "50", f"v_{self.poulets.pk}": "300000",
                                         f"q_{self.mort.pk}": "", "observations": "RAS"})
        self.assertRedirects(r, reverse("accueil"))
        f = Fiche.objects.get(producteur=self.p, semaine=S2)
        self.assertEqual((f.statut, f.total_valeurs, f.observations), (Fiche.SOUMISE, 300000, "RAS"))
        self.assertEqual([(l.produit, l.quantite) for l in f.effectifs.all()], [(self.poulets, 50)])
        self.assertFalse(Fiche.objects.filter(producteur=self.autre).exists())

    def test_valeur_non_numerique_refusee(self):
        r = self.client.post(SAISIE_S2, {f"q_{self.poulets.pk}": "cinquante"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Nombre entier uniquement")
        self.assertFalse(Fiche.objects.filter(semaine=S2).exists())

    def test_fiche_validee_verrouillee(self):
        self.client.post(reverse("saisie_semaine", args=["2026-10-14"]), {f"q_{self.poulets.pk}": "999"})
        self.assertEqual(Fiche.objects.get(semaine=S1).effectifs.get().quantite, 45)

    def test_correction_repasse_a_valider(self):
        f = Fiche.objects.get(semaine=S1)
        f.statut, f.commentaire = Fiche.A_CORRIGER, "Vérifiez le nombre de poulets"
        f.save()
        self.assertContains(self.client.get(reverse("accueil")), "Vérifiez le nombre de poulets")
        self.client.post(reverse("saisie_semaine", args=["2026-10-14"]), {f"q_{self.poulets.pk}": "44",
                                                                          f"v_{self.poulets.pk}": "270000"})
        f.refresh_from_db()
        self.assertEqual((f.statut, f.effectifs.get().quantite), (Fiche.SOUMISE, 44))


class ResponsableTests(TestCase):
    def setUp(self):
        self.r = Responsable.objects.create(nom="M. Traoré", telephone="76000100", utilisateur=compte("76000100"))
        self.mien = creer_producteur("Siaka KEITA", "76000003")
        self.mien.responsable = self.r
        self.mien.save()
        self.autre = creer_producteur("Thara KANOUTE", "76000004")
        self.fiche = Fiche.objects.create(producteur=self.mien, semaine=S1)
        Fiche.objects.create(producteur=self.autre, semaine=S1)
        Depense.objects.create(fiche=self.fiche, date=S1, categorie="aliments", montant=20000)
        self.client.login(username="76000100", password="1234")

    def test_voit_seulement_ses_producteurs_avec_finances(self):
        r = self.client.get(reverse("tableau"))
        self.assertEqual([l["producteur"].nom for l in r.context["lignes"]], ["Siaka KEITA"])
        self.assertEqual(len(r.context["a_valider"]), 1)
        self.assertEqual(r.context["lignes"][0]["depenses"], 20000)
        self.assertNotContains(r, "Secteurs et produits")  # pas de liens d'administration
        self.assertEqual(self.client.get(reverse("fiche_producteur", args=[self.autre.pk])).status_code, 404)

    def test_pas_d_acces_administration(self):
        r = self.client.get(reverse("admin:producteurs_producteur_changelist"))
        self.assertEqual(r.status_code, 302)

    def test_valider(self):
        url = reverse("fiche_producteur", args=[self.mien.pk])
        self.client.post(url, {"semaine": "2026-10-14", "decision": "valider"})
        self.fiche.refresh_from_db()
        self.assertEqual(self.fiche.statut, Fiche.VALIDEE)
        self.assertEqual(self.fiche.valide_par.username, "76000100")

    def test_correction_exige_un_commentaire(self):
        url = reverse("fiche_producteur", args=[self.mien.pk])
        r = self.client.post(url, {"semaine": "2026-10-14", "decision": "corriger"})
        self.assertContains(r, "Expliquez au producteur")
        self.client.post(url, {"semaine": "2026-10-14", "decision": "corriger", "commentaire": "Il manque les œufs"})
        self.fiche.refresh_from_db()
        self.assertEqual((self.fiche.statut, self.fiche.commentaire), (Fiche.A_CORRIGER, "Il manque les œufs"))


class RapportTests(TestCase):
    def setUp(self):
        call_command("charger_fiches_excel", verbosity=0)
        get_user_model().objects.create_superuser("chef", password="secret-123", first_name="Chef")
        self.client.login(username="chef", password="secret-123")
        self.octobre = "?periode=libre&debut=2026-10-01&fin=2026-10-31"

    def test_bornes_des_periodes(self):
        from .rapports import bornes
        j = date(2026, 10, 22)
        self.assertEqual(bornes("mois", j), (date(2026, 10, 1), date(2026, 10, 31)))
        self.assertEqual(bornes("mois_precedent", j), (date(2026, 9, 1), date(2026, 9, 30)))
        self.assertEqual(bornes("trimestre", j), (date(2026, 10, 1), date(2026, 12, 31)))
        self.assertEqual(bornes("libre", j, date(2026, 10, 20), date(2026, 10, 1)), (date(2026, 10, 1), date(2026, 10, 20)))

    def test_rapport_du_mois(self):
        r = self.client.get(reverse("rapport") + self.octobre)
        self.assertEqual(r.status_code, 200)
        tot = r.context["tot"]
        self.assertEqual((tot["nb"], tot["depenses"], tot["ventes"]), (34, 428_000, 198_500))
        alpha = next(l for l in r.context["lignes"] if l["producteur"].nom == "Alpha GANO")
        self.assertEqual((alpha["debut"], alpha["fin"]), (3_556_600, 3_705_500))  # 1er octobre → 14 octobre
        self.assertEqual(alpha["evo"]["ecart"], 148_900)
        self.assertEqual(len(r.context["courbe"]["points"]), 3)
        # Thara KANOUTE n'a pas de fiche avant le 14 : pas de valeur de départ dans le total.
        self.assertEqual((tot["debut"], tot["fin"]), (6_289_600, 6_430_000))

    def test_rapport_imprimable(self):
        r = self.client.get(reverse("rapport_imprimable") + self.octobre)
        self.assertContains(r, "Suivi des producteurs — Octobre 2026")
        self.assertContains(r, "CIAF/CE · Centre d&#x27;Incubation Agroforestière Champ École")
        self.assertContains(r, "Imprimer ou enregistrer en PDF")
        self.assertContains(r, "Détail par producteur")

    def test_export_excel(self):
        from io import BytesIO

        from openpyxl import load_workbook
        r = self.client.get(reverse("rapport_excel") + self.octobre)
        self.assertEqual(r["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        wb = load_workbook(BytesIO(r.content))
        self.assertEqual(wb.sheetnames[0], "Récapitulatif")
        self.assertEqual(wb["Récapitulatif"]["A1"].value, "CIAF/CE · Suivi des producteurs — Récapitulatif")
        self.assertTrue(wb["Récapitulatif"]["A3"].value.startswith("Centre d'Incubation Agroforestière Champ École"))
        self.assertIn("Alpha GANO", wb.sheetnames)
        self.assertEqual(wb.sheetnames[-4:], ["Dépenses", "Ventes", "Prêts", "Bilan financier"])
        self.assertEqual(wb["Dépenses"].max_row, 5 + 10 + 1)  # en-tête, 10 dépenses, total
        self.assertEqual(wb["Prêts"]["A6"].value, "Aucune opération sur la période.")
        recap = wb["Récapitulatif"]
        self.assertEqual((recap["A6"].value, recap["E6"].value, recap["F6"].value), ("Alpha GANO", 3_556_600, 3_705_500))
        self.assertEqual(recap["G6"].value, '=IF(OR(E6="",F6=""),"",F6-E6)')

    def test_responsable_rapport_limite_a_ses_producteurs(self):
        r = Responsable.objects.create(nom="M. Traoré", telephone="76000100", utilisateur=compte("76000100"))
        Producteur.objects.filter(nom="Alpha GANO").update(responsable=r)
        self.client.login(username="76000100", password="1234")
        rep = self.client.get(reverse("rapport") + self.octobre)
        self.assertEqual([l["producteur"].nom for l in rep.context["lignes"]], ["Alpha GANO"])
        self.assertEqual(rep.context["tot"]["depenses"], 24_500 + 75_000)


class AdministrateurTests(TestCase):
    def setUp(self):
        get_user_model().objects.create_superuser("chef", password="secret-123")
        self.p = creer_producteur("Alpha GANO", "76000001", [produit("Poulets")])
        for s, montant in ((S1, 100000), (S2, 150000)):
            f = Fiche.objects.create(producteur=self.p, semaine=s)
            LigneValeur.objects.create(fiche=f, libelle="Poulets", montant=montant)
        Depense.objects.create(fiche=Fiche.objects.get(semaine=S2), date=S2, categorie="aliments", montant=20000)
        Pret.objects.create(producteur=self.p, date=S2, montant=50000)
        Pret.objects.create(producteur=self.p, date=S2, type=Pret.TYPE_REMBOURSEMENT, montant=10000)
        self.client.login(username="chef", password="secret-123")

    def test_tableau_montre_evolution_et_bilan(self):
        r = self.client.get(reverse("tableau"))
        ligne = r.context["lignes"][0]
        self.assertEqual((ligne["precedent"], ligne["actuel"]), (100000, 150000))
        self.assertEqual(ligne["evo"]["etat"], "hausse")
        self.assertEqual((ligne["resultat"], ligne["prets"]), (-20000, 40000))
        self.assertContains(r, "▲ +50 000 F")

    def test_filtre_par_secteur(self):
        pepiniere = Secteur.objects.get(nom="Pépinière")
        plants = Produit.objects.create(secteur=pepiniere, nom="Plants de manguiers", unite="plants")
        autre = creer_producteur("Pépiniériste", "76000009", [plants])
        Fiche.objects.create(producteur=autre, semaine=S2)
        r = self.client.get(reverse("tableau") + f"?semaine=2026-10-21&secteur={pepiniere.pk}")
        self.assertEqual([l["producteur"].nom for l in r.context["lignes"]], ["Pépiniériste"])
        self.assertEqual(len(self.client.get(reverse("tableau")).context["lignes"]), 2)

    def test_export_csv(self):
        r = self.client.get(reverse("tableau") + "?format=csv")
        self.assertIn("Alpha GANO;À valider;100000;150000;50000;20000;0;-20000;40000", r.content.decode("utf-8-sig"))

    def test_creer_producteur_avec_produits_et_pin(self):
        r = self.client.post(reverse("admin:producteurs_producteur_add"), {
            "nom": "Siaka KEITA", "produits": [produit("Poulets adultes").pk, produit("Poulets moyens").pk],
            "actif": "on", "ordre": "3", "telephone": "+223 66 00 00 03", "code_pin": "4321",
            "prets-TOTAL_FORMS": "0", "prets-INITIAL_FORMS": "0",
        })
        self.assertEqual(r.status_code, 302)
        p = Producteur.objects.get(nom="Siaka KEITA")
        self.assertEqual((p.telephone, p.produits.count()), ("+22366000003", 2))
        self.client.logout()
        self.assertTrue(self.client.login(username="+22366000003", password="4321"))

    def test_creer_responsable_et_attribuer_producteurs(self):
        r = self.client.post(reverse("admin:producteurs_responsable_add"), {
            "nom": "M. Traoré", "actif": "on", "producteurs": [self.p.pk],
            "telephone": "76 00 01 00", "code_pin": "5555"})
        self.assertEqual(r.status_code, 302)
        self.p.refresh_from_db()
        self.assertEqual(self.p.responsable.nom, "M. Traoré")
        self.assertTrue(self.client.login(username="76000100", password="5555"))
