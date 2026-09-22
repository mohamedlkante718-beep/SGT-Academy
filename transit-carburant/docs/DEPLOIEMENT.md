# Déploiement du backend TransitCarburant

Objectif : mettre le backend en ligne quelque part d'accessible depuis
les téléphones des agents, sans VPS et sans coût au démarrage. Ce
guide donne la marche à suivre manuelle (la plus fiable) et une
alternative conteneurisée pour qui préfère s'auto-héberger.

## Ce qui a été vérifié, et ce qui ne l'a pas été

- **Vérifié réellement dans cet environnement** : le backend tourne
  correctement contre une vraie base **PostgreSQL 16** (pas seulement
  SQLite) — bootstrap de l'admin, création de poste avec génération de
  clés Ed25519, synchronisation d'un manifeste signé, upload de photo,
  lecture du tableau de bord : tout fonctionne avec `psycopg2-binary`.
  C'était le principal risque de passer de SQLite (dev) à PostgreSQL
  (production).
- **Non vérifié** : la construction de l'image Docker elle-même. Cet
  environnement de développement bloque, par politique réseau, l'accès
  à `production.cloudfront.docker.com` (le CDN utilisé par Docker Hub
  pour servir les images) — sans rapport avec les serveurs de Render,
  qui construisent en dehors de cet environnement et ne sont pas
  concernés par cette restriction. Le `Dockerfile` suit un schéma
  standard (Python 3.11 + FastAPI + uvicorn) mais n'a pas pu être
  construit ici : à valider une fois poussé, avant de s'y fier pour un
  déploiement auto-hébergé.

## Option recommandée : Render (service web) + base gratuite externe

Render n'exige pas de carte bancaire pour son tier gratuit de service
web, mais son offre PostgreSQL gratuite est limitée dans le temps
selon les régions/comptes. Le plus fiable et gratuit durablement :
héberger la base ailleurs (Neon ou Supabase, PostgreSQL géré,
tiers gratuits pérennes) et le service web sur Render.

### 1. Créer la base de données (Neon ou Supabase)

1. Créer un compte sur [neon.tech](https://neon.tech) (ou
   [supabase.com](https://supabase.com)).
2. Créer un projet / une base PostgreSQL.
3. Récupérer la chaîne de connexion (`postgresql://user:password@host/dbname`
   — Neon/Supabase donnent ce format directement, avec `?sslmode=require`
   à conserver).

### 2. Créer le service web sur Render

1. Créer un compte sur [render.com](https://render.com) et connecter le
   dépôt GitHub `sgt-academy`.
2. **New > Web Service**, choisir ce dépôt.
3. **Root Directory** : `transit-carburant/backend`
4. **Runtime** : Python 3
5. **Build Command** : `pip install -r requirements.txt`
6. **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. **Plan** : Free
8. Variables d'environnement (section *Environment*) :

   | Variable | Valeur |
   |---|---|
   | `DATABASE_URL` | la chaîne de connexion Neon/Supabase de l'étape 1 |
   | `JWT_SECRET` | une longue chaîne aléatoire (ex. générée avec `openssl rand -hex 32`) |
   | `ADMIN_BOOTSTRAP_MATRICULE` | `admin` (ou autre) |
   | `ADMIN_BOOTSTRAP_PASSWORD` | un mot de passe fort — **à changer** après la première connexion s'il n'y a pas encore de gestion de changement de mot de passe |

9. Déployer. Render construit et démarre le service ; l'URL publique
   (`https://transit-carburant-api.onrender.com` ou similaire) est
   celle à utiliser comme `API_BASE_URL` côté mobile.

### Limite connue : le tier gratuit s'endort

Un service web gratuit Render se met en veille après 15 minutes sans
requête, et met quelques dizaines de secondes à se réveiller à la
requête suivante. Acceptable pour un pilote (les agents toléreront un
premier essai de synchronisation lent après une pause), mais à
surveiller : si ça devient gênant, un plan payant d'entrée de gamme
supprime la mise en veille.

### Limite connue : le stockage des photos n'est pas persistant

Le tier gratuit de Render ne propose pas de disque persistant : les
photos uploadées (`MEDIA_ROOT`, servies sous `/media/`) disparaissent à
chaque redéploiement. Deux options quand ça devient un problème réel :
- passer sur un plan Render avec disque persistant (payant, simple à
  activer, aucune modification de code) ;
- migrer le stockage vers un service compatible S3 (ex. Cloudflare R2,
  tier gratuit généreux) — nécessite d'adapter
  `backend/app/routers/sync.py::uploader_photo_manifeste` pour écrire
  vers ce service au lieu du disque local.

## Alternative : auto-hébergement avec Docker

Pour qui préfère garder la main (VPS personnel, serveur local, Fly.io,
etc.), `backend/Dockerfile` et `backend/docker-compose.yml` fournissent
une stack complète (API + PostgreSQL) :

```bash
cd backend
docker compose up --build
```

Expose l'API sur `http://localhost:8000` avec une base PostgreSQL
locale. Comme indiqué plus haut, cette image n'a pas pu être construite
dans cet environnement de développement (réseau restreint) — à tester
sur une machine avec un accès normal à Docker Hub avant de s'y fier.

## Connecter l'application mobile au backend déployé

Une fois l'URL Render (ou autre) connue :

```bash
flutter run --dart-define=API_BASE_URL=https://transit-carburant-api.onrender.com
```

ou, pour un build de production, passer la même option à
`flutter build apk`.
