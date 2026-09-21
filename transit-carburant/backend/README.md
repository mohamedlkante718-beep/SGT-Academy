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

## Tests

```bash
pytest -v
```

Les tests couvrent le parcours complet (création de poste avec
génération de clés Ed25519, création des comptes agents, envoi d'un
manifeste signé, idempotence de la synchronisation, contrôle dépôt,
et lecture du tableau de bord), ainsi que le rejet d'une signature
invalide. Validés dans cet environnement : `3 passed`.

## Hébergement à très faible coût

Aucun VPS n'est nécessaire pour démarrer : ce service est un simple
service web stateless + une base de données, déployable sur les tiers
gratuits de Render ou Fly.io (voir la section "Contrainte financière"
du cahier des charges).
