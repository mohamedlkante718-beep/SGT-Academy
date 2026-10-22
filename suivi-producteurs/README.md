# Suivi des producteurs — CIAF

Application de suivi hebdomadaire des producteurs du CIAF.

| Qui | Où | Ce qu'il fait |
|---|---|---|
| **Administrateur** | Ordinateur, page web `/gestion/` | Voit tout : valeur précédente, valeur actuelle, évolution (▲ hausse / ▼ baisse), dépenses, ventes, résultat net, prêts en cours. Il est le seul à créer les producteurs et les responsables, à **attribuer à chaque producteur ses produits** (et à les changer), à saisir les dépenses, les ventes et les prêts. Il peut aussi valider les fiches. |
| **Responsable** (ex. M. Traoré) | Ordinateur ou téléphone, même adresse | Voit **uniquement ses producteurs** et leur évolution, et **valide** leurs fiches, ou les renvoie au producteur pour correction avec un commentaire. Il voit aussi les finances et les rapports de ses producteurs, mais ne modifie rien. |
| **Producteur** | Téléphone (application installable) | Se connecte avec son numéro et son code PIN. Il remplit uniquement **les produits que l'administrateur lui a attribués** (quantité et/ou valeur), plus ses observations. Il voit ses chiffres de la semaine d'avant et le statut de ses fiches. |

**Secteurs et produits** : l'administrateur crée autant de secteurs qu'il veut, puis les produits de chaque secteur.
Pour chaque produit, il indique l'unité (têtes, œufs, kg, plants…) et s'il « se compte » (quantité), s'il « a une valeur » (F CFA), ou les deux.
Trois secteurs sont déjà créés :
- **Élevage**, avec les 28 produits de la fiche Excel ;
- **Agriculture**, vide, à compléter avec la fiche de M. Traoré ;
- **Pépinière**, vide, à compléter.

**Circuit d'une fiche** : le producteur envoie sa fiche (statut **À valider**). Le responsable la **valide**, ou demande une
**correction** avec un commentaire que le producteur voit sur son téléphone. Le producteur corrige et renvoie. Une fiche validée
ne peut plus être modifiée par le producteur. L'administrateur peut toujours la corriger dans l'administration.

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
3. **Créer la base, charger les fiches Excel d'octobre (semaines du 1er, du 8 et du 14) et créer le compte administrateur :**
   ```bash
   python manage.py migrate
   python manage.py charger_fiches_excel
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
Cochez **ses produits**, choisissez son **responsable**, saisissez son **téléphone** et un **code PIN** de 4 à 6 chiffres, puis enregistrez. Communiquez-lui l'adresse
du site, son numéro et son code. Les 12 producteurs chargés depuis les fichiers Excel ont un numéro provisoire
« A-COMPLETER-… » : remplacez-le par leur vrai numéro et donnez-leur un code PIN.

**Installer sur le téléphone** : le producteur ouvre l'adresse du site dans Chrome, se connecte, puis choisit
**⋮ → Ajouter à l'écran d'accueil**. Une icône « Suivi CIAF » apparaît comme une application.

**Ajouter un secteur ou un produit** : dans l'administration, ouvrez **Secteurs et produits**. Cliquez sur **Ajouter**
pour un nouveau secteur, ou ouvrez un secteur et remplissez une ligne vide en bas (nom, unité, « se compte », « a une valeur »).
Ensuite, dans **Producteurs**, cochez ce produit pour les producteurs concernés : il apparaît aussitôt sur leur téléphone.
Pour retirer un produit sans perdre l'historique, décochez « actif ».

**Créer un responsable** : dans **Responsables** → **Ajouter**, saisissez son nom, son téléphone et un code PIN, puis cochez
les producteurs qu'il suit. Il se connecte à la même adresse que les producteurs et arrive sur « Mes producteurs ».

**Dépenses et ventes** : dans **Fiches, dépenses et ventes**, ouvrez la fiche du producteur pour la semaine,
puis remplissez les lignes « Dépenses » et « Ventes » en bas de la page.

**Prêts** : dans **Prêts**, ajoutez chaque prêt ou avance accordé et chaque remboursement reçu.
Le tableau de bord calcule le montant restant dû.

**Rapports** (menu **Rapports**, pour l'administrateur et les responsables, chacun sur ses producteurs) :
choisissez une période (ce mois-ci, le mois dernier, ce trimestre, cette année ou des dates libres) et, si besoin, un secteur.
Le rapport donne pour chaque producteur la valeur au début et à la fin de la période, l'évolution, les dépenses, les ventes,
le résultat net et les prêts, avec la courbe semaine par semaine et les dépenses par catégorie. Ensuite :
- **Version imprimable / PDF** : une page A4 avec en plus le détail produit par produit de chaque producteur.
  Bouton « Imprimer ou enregistrer en PDF », puis choisissez « Enregistrer au format PDF » comme imprimante.
- **Télécharger le fichier Excel** : un classeur dans l'esprit du fichier CIAF. Il contient un récapitulatif, une feuille
  par producteur (semaine par semaine), et les feuilles Dépenses, Ventes, Prêts et Bilan financier, avec des formules.

Le tableau de bord garde l'export CSV de la semaine et un lien direct vers le rapport imprimable de la semaine.

## Développement local
```bash
pip install -r requirements.txt
python manage.py migrate && python manage.py charger_fiches_excel && python manage.py createsuperuser
python manage.py runserver
python manage.py test producteurs   # 25 tests
```

## À venir
- **Volet agriculture** : la fiche de suivi agricole de M. Traoré sera intégrée dès réception
  (superficies, cultures, rendements…). En attendant, l'administrateur peut déjà ajouter les produits agricoles
  et de pépinière dans leurs secteurs, et les attribuer aux producteurs.
