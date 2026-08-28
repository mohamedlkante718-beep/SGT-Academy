# SGT Academy — Backend (Django + DRF)

Configuration, apps Django, modèles et API couvrant tout le parcours MVP décrit dans [`../docs/01-ANALYSE-ARCHITECTURE.md`](../docs/01-ANALYSE-ARCHITECTURE.md) : visiteur → catalogue → compte → achat (paiement manuel) → accès → cours → progression → quiz → examen → certificat → vérification publique.

## Ce qui n'est PAS encore réel (§53 : jamais simulé comme fonctionnel)

- **Mobile Money / carte bancaire** : refusés explicitement (HTTP 501) tant qu'aucun prestataire (CinetPay/PayDunya/Kkiapay/FedaPay...) n'est contractualisé et configuré. Seul le **paiement manuel** débloque réellement l'accès aujourd'hui.
- **PDF du certificat** (mise en page, logo, signature) : non généré. Seuls l'enregistrement en base et le QR code (image PNG réelle, pointant vers `/verify/{code}`) sont produits.
- **Emails/SMS de notification** : aucun envoi réel.
- **Stockage S3** : fonctionne en local sur disque ; le branchement à un vrai bucket (R2/B2/S3) se fait via les variables `AWS_*` en production, non testé faute d'identifiants.

## API disponible (v0.3 — parcours complet MVP)

| Méthode | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | Créer un compte apprenant (§10) | Non |
| POST | `/api/v1/auth/login/` | Connexion, retourne access + refresh JWT | Non |
| POST | `/api/v1/auth/refresh/` | Renouveler l'access token | Non |
| POST | `/api/v1/auth/logout/` | Invalide le refresh token (blacklist) | Oui |
| GET | `/api/v1/auth/me/` | Profil de l'utilisateur connecté | Oui |
| GET | `/api/v1/courses/` | Catalogue public (filtres, recherche, tri) | Non |
| GET | `/api/v1/courses/{slug}/` | Détail d'une formation publiée + programme | Non |
| POST | `/api/v1/courses/{slug}/purchase/` | Démarre l'achat (paiement manuel opérationnel ; coupon optionnel) | Oui |
| GET | `/api/v1/payments/{reference}/` | Statut d'un paiement (propriétaire) | Oui |
| PATCH | `/api/v1/payments/{reference}/proof/` | Soumettre référence/preuve de paiement manuel | Oui |
| GET | `/api/v1/my-courses/` | Mes formations + progression (§13) | Oui |
| GET | `/api/v1/courses/{slug}/progress/` | Programme détaillé + statut par leçon (accès réservé aux inscrits) | Oui |
| POST | `/api/v1/lessons/{id}/complete/` | Marquer une leçon terminée (met à jour la progression) | Oui |
| GET | `/api/v1/quizzes/{id}/` | Questions d'un quiz (sans les bonnes réponses) | Oui (inscrit) |
| POST | `/api/v1/quizzes/{id}/submit/` | Corrige immédiatement, renvoie le score | Oui (inscrit) |
| POST | `/api/v1/exams/{id}/start/` | Démarre une tentative d'examen (respecte le nombre max) | Oui (inscrit) |
| POST | `/api/v1/exams/{id}/submit/` | Corrige l'examen ; déclenche le certificat si réussi | Oui (inscrit) |
| GET | `/api/v1/certificates/` | Mes certificats | Oui |
| GET | `/api/v1/certificates/{id}/` | Détail (propriétaire uniquement) | Oui |
| GET | `/api/v1/certificates/verify/{code}/` | Vérification publique (§19), limitée à 30 req/min | Non |

Points de sécurité déjà en place : un paiement `pending` ne débloque jamais l'accès (seul un passage serveur à `PAID` le fait, via signal) ; les leçons hors aperçu sont invisibles/non complétables sans inscription ; un quiz/examen refuse l'accès si l'utilisateur n'est pas inscrit ; les bonnes réponses ne sont jamais envoyées au navigateur ; un certificat n'est consultable en détail que par son propriétaire, mais la vérification par code reste publique et journalisée.

Documentation interactive : `/api/docs/`.

Tests : `python manage.py test` — **38 tests, tous verts**, couvrant notamment : accès refusé aux formations non payées, paiement `pending` ne débloquant rien, double-soumission d'examen bloquée, nombre max de tentatives respecté, certificat émis automatiquement à la réussite, code de vérification unique, formation brouillon invisible publiquement.

## Apps Django

| App | Contenu |
|---|---|
| `apps.common` | Modèles de base (UUID, horodatage, soft delete), `AuditLog`, `Setting` |
| `apps.accounts` | `User` (auth par email), `Role`, `Permission`, `UserRole`, `Profile` |
| `apps.courses` | `Category`, `Course`, `Module`, `Lesson`, `LessonResource`, `Instructor` |
| `apps.learning` | `Enrollment`, `LessonProgress`, `CourseProgress` |
| `apps.assessments` | `Quiz`, `Exam`, `Question`, `Answer`, `QuizAttempt`, `QuizResult`, `ExamAttempt` |
| `apps.payments` | `Payment`, `PaymentTransaction` (+ signal qui crée l'inscription quand un paiement passe à `PAID`) |
| `apps.coupons` | `Coupon`, `CouponUsage` |
| `apps.certificates` | `Certificate`, `CertificateVerification` |
| `apps.companies` | `Company`, `CompanyUser`, `CompanyLicense` (schéma prêt, fonctionnalités B2B en V2) |
| `apps.notifications` | `Notification` |
| `apps.reviews` | `Review` |

## Installation locale (Windows, étape par étape)

1. **Installer Python 3.12+** : téléchargez sur [python.org](https://www.python.org/downloads/), cochez "Add Python to PATH" pendant l'installation.
2. **Installer Git** : [git-scm.com](https://git-scm.com/download/win).
3. **Cloner le dépôt** :
   ```
   git clone https://github.com/mohamedlkante718-beep/sgt-academy.git
   cd sgt-academy/backend
   ```
4. **Créer un environnement virtuel** (isole les dépendances Python du projet) :
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
   Vous devez voir `(.venv)` apparaître au début de votre invite de commande.
5. **Installer les dépendances** :
   ```
   pip install -r requirements.txt
   ```
6. **Créer votre fichier `.env`** à partir du modèle :
   ```
   copy .env.example .env
   ```
   Ouvrez `.env` et générez une vraie `SECRET_KEY` (une longue chaîne aléatoire). Sans PostgreSQL installé, laissez `DATABASE_URL` vide : le projet utilisera automatiquement SQLite pour développer localement.
7. **(Optionnel) Installer PostgreSQL** si vous voulez tester avec la vraie base de données cible : [postgresql.org/download/windows](https://www.postgresql.org/download/windows/), créez une base `sgt_academy`, puis renseignez `DATABASE_URL` dans `.env` (ex: `postgres://postgres:motdepasse@localhost:5432/sgt_academy`).
8. **Appliquer les migrations** :
   ```
   python manage.py migrate
   ```
9. **Créer un compte super administrateur** :
   ```
   python manage.py createsuperuser
   ```
10. **Démarrer le serveur** :
    ```
    python manage.py runserver
    ```
11. **Tester** : ouvrez `http://127.0.0.1:8000/admin/` (connexion avec le superuser créé) et `http://127.0.0.1:8000/api/docs/` (documentation API interactive, vide pour l'instant).

## Erreurs possibles

- **`'django' n'est pas reconnu...`** → l'environnement virtuel n'est pas activé, ou l'installation a échoué. Relancez `pip install -r requirements.txt`.
- **Erreur de connexion PostgreSQL** → vérifiez que le service PostgreSQL est démarré et que `DATABASE_URL` correspond exactement à vos identifiants, ou laissez `DATABASE_URL` vide pour utiliser SQLite en attendant.
- **`SECRET_KEY manquant`** → le fichier `.env` n'existe pas ou est vide ; recopiez `.env.example`.

## Prochaine étape

Ajout des routes API (`/api/v1/...`) : inscription/connexion (JWT), catalogue de formations, achat, progression, quiz/examen, certificats — app par app, avec tests, plutôt que tout d'un coup.
