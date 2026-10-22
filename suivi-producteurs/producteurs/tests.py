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


class PagesGestionTests(TestCase):
    """Les pages de gestion restent dans l'application (pas l'administration Django)."""

    def setUp(self):
        get_user_model().objects.create_superuser("chef", password="secret-123")
        self.client.login(username="chef", password="secret-123")
        self.p = creer_producteur("Alpha GANO", "76000001", [produit("Poulets")])
        self.fiche = Fiche.objects.create(producteur=self.p, semaine=S1)

    def test_pages_accessibles_et_menu_interne(self):
        for nom in ("producteurs", "responsables", "secteurs", "prets", "producteur_ajouter", "responsable_ajouter",
                    "secteur_ajouter"):
            r = self.client.get(reverse(nom))
            self.assertEqual(r.status_code, 200, nom)
            self.assertNotContains(r, "/admin/producteurs/")
        self.assertEqual(self.client.get(reverse("finances", args=[self.fiche.pk])).status_code, 200)

    def test_ajouter_producteur(self):
        r = self.client.post(reverse("producteur_ajouter"), {
            "nom": "Sada COULIBALY", "telephone": "76 11 22 33", "code_pin": "2468",
            "produits": [produit("Poulets").pk], "actif": "on", "ordre": "13"})
        self.assertRedirects(r, reverse("producteurs"))
        p = Producteur.objects.get(nom="Sada COULIBALY")
        self.assertEqual((p.telephone, p.produits.count()), ("76112233", 1))
        self.client.logout()
        self.assertTrue(self.client.login(username="76112233", password="2468"))

    def test_modifier_produits_sans_changer_le_pin(self):
        r = self.client.post(reverse("producteur_modifier", args=[self.p.pk]), {
            "nom": "Alpha GANO", "telephone": "76000001", "code_pin": "",
            "produits": [produit("Pintades").pk, produit("Dindes").pk], "actif": "on", "ordre": "1"})
        self.assertRedirects(r, reverse("producteurs"))
        self.assertEqual(sorted(x.nom for x in self.p.produits.all()), ["Dindes", "Pintades"])
        self.client.logout()
        self.assertTrue(self.client.login(username="76000001", password="1234"))

    def test_responsable_et_ses_producteurs(self):
        r = self.client.post(reverse("responsable_ajouter"), {
            "nom": "M. Traoré", "telephone": "76000100", "code_pin": "5555", "actif": "on", "producteurs": [self.p.pk]})
        self.assertRedirects(r, reverse("responsables"))
        self.p.refresh_from_db()
        self.assertEqual(self.p.responsable.nom, "M. Traoré")

    def test_secteur_pepiniere_avec_produits(self):
        pep = Secteur.objects.get(nom="Pépinière")
        data = {"nom": "Pépinière", "ordre": "3", "actif": "on",
                "produits-TOTAL_FORMS": "3", "produits-INITIAL_FORMS": "0",
                "produits-0-nom": "Plants de manguiers", "produits-0-unite": "plants", "produits-0-compter": "on",
                "produits-0-valoriser": "on", "produits-0-ordre": "1", "produits-0-actif": "on",
                "produits-1-ordre": "0", "produits-1-actif": "on", "produits-1-compter": "on", "produits-1-valoriser": "on",
                "produits-2-ordre": "0", "produits-2-actif": "on", "produits-2-compter": "on", "produits-2-valoriser": "on"}
        r = self.client.post(reverse("secteur_modifier", args=[pep.pk]), data)
        self.assertRedirects(r, reverse("secteurs"))
        self.assertEqual(list(pep.produits.values_list("nom", flat=True)), ["Plants de manguiers"])
        r = self.client.get(reverse("producteur_modifier", args=[self.p.pk]))
        self.assertContains(r, "Plants de manguiers")

    def test_saisir_depenses_et_ventes(self):
        url = reverse("finances", args=[self.fiche.pk])
        data = {"depenses-TOTAL_FORMS": "2", "depenses-INITIAL_FORMS": "0",
                "depenses-0-date": "2026-10-15", "depenses-0-categorie": "aliments", "depenses-0-montant": "25000",
                "depenses-0-description": "Aliment démarrage",
                "depenses-1-date": "2026-10-14",
                "ventes-TOTAL_FORMS": "2", "ventes-INITIAL_FORMS": "0",
                "ventes-0-date": "2026-10-16", "ventes-0-categorie": "Aviculture", "ventes-0-montant": "40000",
                "ventes-1-date": "2026-10-14"}
        r = self.client.post(url, data)
        self.assertRedirects(r, reverse("fiche_producteur", args=[self.p.pk]) + "?semaine=2026-10-14")
        self.fiche.refresh_from_db()
        self.assertEqual((self.fiche.total_depenses, self.fiche.total_ventes), (25000, 40000))

    def test_prets(self):
        self.client.post(reverse("prets"), {"producteur": self.p.pk, "date": "2026-10-20", "type": "pret",
                                            "montant": "100000", "description": "Achat poussins"})
        self.client.post(reverse("prets"), {"producteur": self.p.pk, "date": "2026-10-21", "type": "remboursement",
                                            "montant": "30000"})
        r = self.client.get(reverse("prets"))
        self.assertEqual(r.context["total"], 70000)
        self.client.post(reverse("prets"), {"supprimer": Pret.objects.get(type="remboursement").pk})
        self.assertEqual(self.p.prets_en_cours(), 100000)

    def test_responsable_n_a_pas_acces(self):
        Responsable.objects.create(nom="R", telephone="76000200", utilisateur=compte("76000200"))
        self.client.login(username="76000200", password="1234")
        self.assertRedirects(self.client.get(reverse("producteurs")), reverse("tableau"))


class LogoTests(TestCase):
    def setUp(self):
        import tempfile
        from django.test import override_settings
        self.dossier = tempfile.mkdtemp()
        self.reglage = override_settings(MEDIA_ROOT=self.dossier)
        self.reglage.enable()
        get_user_model().objects.create_superuser("chef", password="secret-123")
        self.client.login(username="chef", password="secret-123")

    def tearDown(self):
        import shutil
        self.reglage.disable()
        shutil.rmtree(self.dossier, ignore_errors=True)

    def test_envoyer_le_logo_depuis_l_administration(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import Parametres
        self.assertNotContains(self.client.get(reverse("tableau")), 'class="logo"')
        image = SimpleUploadedFile("logo-ciaf.png", b"\x89PNG\r\n\x1a\n" + b"0" * 100, content_type="image/png")
        r = self.client.post(reverse("admin:producteurs_parametres_add"), {"logo": image})
        self.assertEqual(r.status_code, 302)
        url = Parametres.objects.get().logo.url
        self.assertContains(self.client.get(reverse("tableau")), f'<img class="logo" src="{url}"')
        self.client.logout()
        self.assertContains(self.client.get(reverse("connexion")), 'class="logo-connexion"')
        self.assertEqual(self.client.get(url).status_code, 200)
        # Une seule ligne de réglages : pas de deuxième « Ajouter ».
        self.client.login(username="chef", password="secret-123")
        self.assertEqual(self.client.get(reverse("admin:producteurs_parametres_add")).status_code, 403)

    def test_fichier_refuse(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        r = self.client.post(reverse("admin:producteurs_parametres_add"),
                             {"logo": SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "extension")


class SuppressionTests(TestCase):
    def setUp(self):
        self.p = creer_producteur("Alpha GANO", "76000001", [produit("Poulets")])
        self.fiche = Fiche.objects.create(producteur=self.p, semaine=S1)
        LigneValeur.objects.create(fiche=self.fiche, libelle="Poulets", montant=1000)

    def test_producteur_supprime_sa_fiche_non_validee(self):
        self.client.login(username="76000001", password="1234")
        url = reverse("saisie_supprimer", args=["2026-10-14"])
        self.assertContains(self.client.get(url), "Oui, supprimer")
        self.assertTrue(Fiche.objects.exists())  # rien n'est supprimé sans confirmation
        self.assertRedirects(self.client.post(url), reverse("accueil"))
        self.assertFalse(Fiche.objects.exists())

    def test_producteur_ne_supprime_pas_une_fiche_validee(self):
        self.fiche.statut = Fiche.VALIDEE
        self.fiche.save()
        self.client.login(username="76000001", password="1234")
        self.client.post(reverse("saisie_supprimer", args=["2026-10-14"]))
        self.assertTrue(Fiche.objects.exists())

    def test_producteur_ne_supprime_pas_la_fiche_d_un_autre(self):
        creer_producteur("Autre", "76000002")
        self.client.login(username="76000002", password="1234")
        self.assertEqual(self.client.post(reverse("saisie_supprimer", args=["2026-10-14"])).status_code, 404)
        self.assertTrue(Fiche.objects.exists())

    def test_administrateur_supprime_meme_validee(self):
        self.fiche.statut = Fiche.VALIDEE
        self.fiche.save()
        get_user_model().objects.create_superuser("chef", password="secret-123")
        self.client.login(username="chef", password="secret-123")
        url = reverse("fiche_supprimer", args=[self.fiche.pk])
        self.assertContains(self.client.get(url), "Oui, supprimer définitivement")
        self.assertRedirects(self.client.post(url), reverse("fiche_producteur", args=[self.p.pk]))
        self.assertFalse(Fiche.objects.exists())

    def test_responsable_ne_supprime_pas(self):
        r = Responsable.objects.create(nom="R", telephone="76000200", utilisateur=compte("76000200"))
        self.p.responsable = r
        self.p.save()
        self.client.login(username="76000200", password="1234")
        self.client.post(reverse("fiche_supprimer", args=[self.fiche.pk]))
        self.assertTrue(Fiche.objects.exists())
