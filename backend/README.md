# SGT Academy — Backend (Django + DRF)

Squelette du backend : configuration, apps Django et modèles correspondant au schéma de base de données défini dans [`../docs/01-ANALYSE-ARCHITECTURE.md`](../docs/01-ANALYSE-ARCHITECTURE.md). Aucune route API métier, aucun paiement réel, aucun envoi d'email n'est encore implémenté — c'est l'étape suivante.

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
