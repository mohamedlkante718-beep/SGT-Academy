# SGT Academy

Plateforme professionnelle de formation en ligne (e-learning) de **Safe Green Tech**.

> « Bâtissons un avenir meilleur »

Lancement au Mali, conçue dès le départ pour être accessible dans plusieurs pays d'Afrique francophone (Sénégal, Côte d'Ivoire, Burkina Faso, Guinée, Niger, Bénin, Togo, Cameroun...).

## Statut

Analyse et architecture validées (voir [`docs/01-ANALYSE-ARCHITECTURE.md`](docs/01-ANALYSE-ARCHITECTURE.md)). Squelette backend en cours de construction (apps Django + modèles + migrations) — voir [`backend/README.md`](backend/README.md) pour l'installation locale. Pas encore de routes API métier, pas de frontend, pas de mobile.

## Structure

```
sgt-academy/
├── docs/            # documentation et guides
├── backend/         # Django + Django REST Framework (squelette : apps + modèles + migrations)
├── frontend-web/    # Next.js (site public, SEO) — à venir
└── mobile/          # Flutter (mobile + web authentifié) — à venir
```
