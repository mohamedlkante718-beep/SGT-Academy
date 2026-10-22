# Suivi des producteurs — CIAF

Application de suivi hebdomadaire des producteurs du CIAF.

| Qui | Où | Ce qu'il fait |
|---|---|---|
| **Administrateur** | Ordinateur, page web `/gestion/` | Voit le tableau de bord : valeur précédente, valeur actuelle, évolution (▲ hausse / ▼ baisse), dépenses, ventes, résultat net, prêts en cours. Il est le seul à pouvoir ajouter des producteurs, leur donner un code PIN, saisir les dépenses, les ventes et les prêts. |
| **Producteur** | Téléphone (application installable) | Se connecte avec son numéro et son code PIN, et remplit uniquement la fiche de **ses produits** : quantités, valeur, observations. Il choisit ses produits dans la liste de ses secteurs et voit les chiffres de sa semaine précédente. Il ne voit ni les autres producteurs ni les finances. |

**Secteurs et produits** : l'administrateur crée autant de secteurs qu'il veut (Élevage, Agriculture, Maraîchage,
Pisciculture, Apiculture…) et, dans chaque secteur, la liste des produits avec leur unité (têtes, œufs, kg, sacs…).
Chaque producteur est rattaché à un ou plusieurs secteurs : sur son téléphone, il ne voit que les produits de ses secteurs.
Le secteur Élevage est créé automatiquement avec les 28 produits de la fiche Excel. Le secteur Agriculture est créé vide,
en attendant la fiche de M. Traoré.

La semaine de suivi va du **mercredi au mardi**, comme la fiche Excel de référence (du 14 au 20 octobre 2026).
On peut changer ce jour avec la variable `SEMAINE_JOUR_DEBUT`, où 0 = lundi.

## Mise en ligne sur PythonAnywhere (compte `gageetudes`)

> Ces étapes utilisent l'adresse `gageetudes.pythonanywhere.com`. Si cette adresse sert déjà à un autre site,
> créez une nouvelle application web (onglet **Web** → **Add a new web app**) ou demandez conseil avant de la remplacer.

1. **Récupérer le code.** Dans l'onglet **Consoles**, ouvrez une console **Bash** et tapez :
   ```bash
   git clone -b claude/elegant-hypatia-q8zjzt https://github.com/mohamedlkante718-beep/SGT-Academy.git
   cd SGT-Academy/suivi-producteurs
   ```
   Si le dépôt est privé, GitHub demande un identifiant. Mettez votre nom d'utilisateur GitHub et, comme mot de passe,
   un *Personal access token* (GitHub → Settings → Developer settings → Personal access tokens).
2. **Créer l'environnement Python et installer Django :**
   ```bash
   mkvirtualenv suivi --python=python3.13
   pip install -r requirements.txt
   ```
3. **Créer la base, charger la semaine du 14 octobre et créer le compte administrateur :**
   ```bash
   python manage.py migrate
   python manage.py charger_semaine_initiale
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```
4. **Configurer l'application web** (onglet **Web**) :
   - Choisissez **Manual configuration** et Python 3.13, si vous créez une nouvelle application web.
   - **Virtualenv** : `/home/gageetudes/.virtualenvs/suivi`
   - **Source code** : `/home/gageetudes/SGT-Academy/suivi-producteurs`
   - **WSGI configuration file** : ouvrez-le, remplacez tout son contenu par celui de `pythonanywhere_wsgi.py`,
     et remplacez la clé secrète par une longue suite de caractères au hasard.
   - **Static files** : URL `/static/` → dossier `/home/gageetudes/SGT-Academy/suivi-producteurs/staticfiles`
   - **Force HTTPS** : activé. C'est obligatoire pour installer l'application sur le téléphone.
   - Cliquez sur **Reload**.
5. Ouvrez `https://gageetudes.pythonanywhere.com/gestion/` et connectez-vous avec le compte administrateur.

### Mettre à jour plus tard
```bash
cd ~/SGT-Academy && git pull
cd suivi-producteurs && workon suivi
python manage.py migrate && python manage.py collectstatic --noinput
```
Puis cliquez sur **Reload** dans l'onglet **Web**.

## Utilisation

**Donner l'accès à un producteur** : dans l'administration, ouvrez **Producteurs**, puis un producteur ou **Ajouter**.
Saisissez son **téléphone** et un **code PIN** de 4 à 6 chiffres, puis enregistrez. Communiquez-lui l'adresse
du site, son numéro et son code. Les 12 producteurs chargés depuis l'Excel ont un numéro provisoire
« A-COMPLETER-… » : remplacez-le par leur vrai numéro et donnez-leur un code PIN.

**Installer sur le téléphone** : le producteur ouvre l'adresse du site dans Chrome, se connecte, puis choisit
**⋮ → Ajouter à l'écran d'accueil**. Une icône « Suivi CIAF » apparaît comme une application.

**Ajouter un secteur ou un produit** : dans l'administration, ouvrez **Secteurs et produits**. Cliquez sur **Ajouter**
pour un nouveau secteur, ou ouvrez un secteur et remplissez une ligne vide en bas (nom du produit + unité) pour un nouveau
produit. Ensuite, dans **Producteurs**, cochez ce secteur pour les producteurs concernés.
Le produit apparaît aussitôt sur leur téléphone. Pour retirer un produit sans perdre l'historique, décochez « actif ».

**Dépenses et ventes** : dans **Fiches, dépenses et ventes**, ouvrez la fiche du producteur pour la semaine,
puis remplissez les lignes « Dépenses » et « Ventes » en bas de la page.

**Prêts** : dans **Prêts**, ajoutez chaque prêt ou avance accordé et chaque remboursement reçu.
Le tableau de bord calcule le montant restant dû.

**Exporter** : le bouton **Exporter pour Excel** du tableau de bord télécharge le récapitulatif de la semaine.

## Développement local
```bash
pip install -r requirements.txt
python manage.py migrate && python manage.py charger_semaine_initiale && python manage.py createsuperuser
python manage.py runserver
python manage.py test producteurs   # 14 tests
```

## À venir
- **Volet agriculture** : la fiche de suivi agricole de M. Traoré sera intégrée dès réception
  (superficies, cultures, rendements…). En attendant, l'administrateur peut déjà ajouter les produits agricoles
  dans le secteur « Agriculture » et y rattacher des producteurs.
