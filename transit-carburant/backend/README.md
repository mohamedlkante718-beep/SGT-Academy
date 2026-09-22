# TransitCarburant — Backend

API centrale (FastAPI) : agrège les manifestes/contrôles synchronisés
par les appareils agents, distribue les clés publiques des postes
frontière, et sert le tableau de bord de supervision.

Elle n'est jamais un passage obligé pour créer ou vérifier un
manifeste — voir `docs/CAHIER-DES-CHARGES.md` à la racine du projet.

## Installation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer en local

```bash
uvicorn app.main:app --reload
```

Au premier démarrage, un compte administrateur est créé automatiquement
(matricule `admin`, mot de passe `admin1234` par défaut — à changer en
production via les variables d'environnement `ADMIN_BOOTSTRAP_MATRICULE`
et `ADMIN_BOOTSTRAP_PASSWORD`).

Documentation interactive de l'API : http://127.0.0.1:8000/docs

## Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./transit_carburant.db` | `postgresql://...` en production |
| `JWT_SECRET` | `dev-secret-change-me` | **À changer impérativement en production** |
| `ADMIN_BOOTSTRAP_MATRICULE` | `admin` | Matricule du compte admin initial |
| `ADMIN_BOOTSTRAP_PASSWORD` | `admin1234` | Mot de passe du compte admin initial |
| `MEDIA_ROOT` | `./media` | Dossier de stockage des photos uploadées (servi sous `/media`) — à faire pointer vers un disque persistant en production, un service comme Render efface le disque local à chaque redéploiement |

## Tests

```bash
pytest -v
```

Les tests couvrent le parcours complet (création de poste avec
génération de clés Ed25519, création des comptes agents, envoi d'un
manifeste signé, idempotence de la synchronisation, contrôle dépôt,
et lecture du tableau de bord), le rejet d'une signature invalide, la
vérification d'une signature dont la date est au format produit par
l'appli mobile (Dart) plutôt que par Python — un vrai piège
d'interopérabilité trouvé et corrigé pendant le développement (voir
`docs/DB-SCHEMA.md`) — et l'upload de la photo d'un manifeste (formats
acceptés, rejet, authentification). Chaque test tourne sur sa propre
base isolée (voir `tests/conftest.py`) : un test ne peut jamais fausser
le résultat d'un autre en partageant des données. Validés dans cet
environnement : `8 passed`.

Un test supplémentaire, `tests/test_postgres_compat.py`, rejoue le
parcours complet sur une vraie base **PostgreSQL** plutôt que SQLite
(ignoré par défaut, activé avec `TEST_DATABASE_URL=postgresql://...`)
— c'est celui qui a servi à valider le passage en production, avec un
PostgreSQL 16 réel installé dans l'environnement de développement.

**À faire avant la production** : `MEDIA_ROOT` pointe par défaut vers
un dossier local — sur un hébergeur comme Render, le disque n'est pas
persistant entre redéploiements, il faudra soit un disque persistant
payant, soit migrer vers un stockage objet compatible S3 (ex. Cloudflare
R2, dont le tier gratuit couvre largement les besoins d'un pilote).

## Hébergement à très faible coût

Aucun VPS n'est nécessaire pour démarrer : ce service est un simple
service web stateless + une base de données, déployable sur les tiers
gratuits de Render ou Fly.io. Voir `docs/DEPLOIEMENT.md` pour la
marche à suivre complète (Render + base PostgreSQL gratuite externe),
et la section "Contrainte financière" du cahier des charges pour le
raisonnement d'ensemble.
