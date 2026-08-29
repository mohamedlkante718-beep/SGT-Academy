# SGT Academy — Site public (Next.js)

Le site public/SEO : accueil, catalogue des formations, page détail, inscription/connexion,
tarifs, contact, vérification publique de certificat. Voir [`../docs/01-ANALYSE-ARCHITECTURE.md`](../docs/01-ANALYSE-ARCHITECTURE.md)
pour la justification de ce choix technique (Next.js plutôt que Flutter Web, pour le SEO).

L'espace connecté (tableau de bord apprenant, lecteur de cours, quiz/examen) n'est **pas**
construit ici : il est prévu en Flutter (mobile + web), séparément, car sans enjeu SEO.

## Pages disponibles

| Route | Contenu |
|---|---|
| `/` | Accueil : message principal, formations populaires (API), avantages, appel à l'action |
| `/formations` | Catalogue avec recherche et filtres (niveau, prix, certificat) |
| `/formations/{slug}` | Détail d'une formation, programme, et achat (paiement manuel) |
| `/connexion` | Connexion (JWT) |
| `/inscription` | Création de compte |
| `/tarifs` | Formules (individuel, pack, entreprise) |
| `/contact` | Coordonnées — **espace réservé**, coordonnées réelles et formulaire à brancher avant mise en ligne (§49) |
| `/verify` puis `/verify/{code}` | Vérification publique d'un certificat |

## Ce qui n'est pas encore réel

- Le formulaire de contact est statique (aucun envoi réel).
- L'authentification stocke les tokens JWT en `localStorage` (simple pour le MVP ; à
  revoir en V2 pour une plus grande robustesse face au XSS).
- Aucune image de couverture réelle pour les formations (pas encore de stockage S3 branché).

## Installation locale (Windows, étape par étape)

1. **Installer Node.js** (version 20 ou plus) : [nodejs.org](https://nodejs.org/) — cochez l'option d'ajout au PATH si proposée.
2. **Cloner le dépôt** (si ce n'est pas déjà fait) :
   ```
   git clone https://github.com/mohamedlkante718-beep/sgt-academy.git
   cd sgt-academy/frontend-web
   ```
3. **Installer les dépendances** :
   ```
   npm install
   ```
4. **Créer votre fichier `.env.local`** :
   ```
   copy .env.local.example .env.local
   ```
   Par défaut, il pointe vers `http://127.0.0.1:8000/api/v1` — assurez-vous que le
   backend Django tourne à cette adresse (voir `../backend/README.md`).
5. **Démarrer le site en développement** :
   ```
   npm run dev
   ```
6. **Tester** : ouvrez `http://localhost:3000` dans votre navigateur. Le backend doit
   être démarré (`python manage.py runserver`) et contenir au moins une formation
   publiée pour que le catalogue affiche quelque chose.

## Déploiement sur Railway (pour avoir un vrai lien, sans rien installer)

Même projet Railway que le backend et l'app mobile — encore un service.

1. Sur le tableau de bord Railway, dans le projet `SGT-Academy` : **« + New »** → **« GitHub Repo »** → choisissez à nouveau `SGT-Academy`.
2. Sur ce nouveau service → **Settings** → **Root Directory** : `frontend-web`.
3. Toujours **Settings** → **Variables** → ajoutez :
   - `NEXT_PUBLIC_API_BASE_URL` = `https://sgt-academy-production.up.railway.app/api/v1` (l'adresse de votre backend déjà en ligne)
4. **Settings** → **Networking** → **« Generate Domain »** → port **`3000`**.
5. Attendez le déploiement (icône verte), puis ouvrez l'adresse générée.

Railway détecte automatiquement qu'il s'agit d'un projet Next.js (pas besoin de Dockerfile ici) et exécute `npm install`, `npm run build` puis `npm run start`.

## Erreurs possibles

- **« Le catalogue n'a pas pu être chargé »** sur la page d'accueil/catalogue → le backend
  Django n'est pas démarré, ou `NEXT_PUBLIC_API_BASE_URL` ne correspond pas à son adresse réelle.
- **Erreur CORS dans la console du navigateur** → le backend autorise déjà toutes les
  origines en développement comme en production (`CORS_ALLOW_ALL_ORIGINS`), donc ceci ne
  devrait plus arriver ; si ça arrive quand même, vérifiez que le backend a bien redéployé
  après ce changement.
