# SGT ACADEMY — Analyse & Architecture (phase de cadrage)

**Propriétaire :** Safe Green Tech — « Bâtissons un avenir meilleur »
**Statut :** Document de cadrage, avant tout développement. Aucun code n'a été écrit.
**Dépôt :** `mohamedlkante718-beep/sgt-academy` — projet indépendant, séparé du dépôt `GestionFlotte` (gestion de flotte véhicules, non lié à ce projet).
**Marchés :** lancement au Mali, conçu dès le départ pour être accessible et utilisable dans plusieurs pays d'Afrique francophone (multi-pays, multi-devises, multilingue — voir §36 du cahier des charges, repris en section A et C).

---

## A. Analyse du projet

**Nature :** marketplace + LMS (Learning Management System) B2C/B2B, avec paiement en ligne, certification vérifiable, et volet IA pédagogique.

**Contraintes structurantes du marché cible (Mali → Afrique francophone) :**
- Connexions internet souvent lentes/coûteuses → priorité à la légèreté (pages rapides, vidéos adaptatives, PDF optimisés, peu de JS inutile).
- Paiement dominant : Mobile Money (Orange Money, Moov/Flooz) plus que carte bancaire.
- Téléphones Android d'entrée de gamme majoritaires → l'app mobile doit rester légère.
- Multi-pays/multi-devises dès la conception, même si le lancement est mono-pays (Mali, XOF, FR).

**Parcours critique (à optimiser en nombre de clics) :**
Visiteur → Formation → Compte → Paiement → Accès → Cours → Quiz/Examen → Certificat → Vérification publique.

**Décision de périmètre :** SGT Academy est un projet neuf, séparé de GestionFlotte. Aucune ressource de GestionFlotte n'est modifiée.

---

## B. Architecture technique complète

```
                         ┌───────────────────────────┐
                         │   Site public (SEO)       │  Next.js (React)
                         │ accueil / catalogue /     │  SSR/SSG, léger, indexable
                         │ détail formation / tarifs │
                         └─────────────┬─────────────┘
                                       │ REST/JSON (HTTPS)
┌───────────────┐        ┌────────────▼─────────────┐        ┌───────────────┐
│ App mobile     │◄──────┤   Backend API             ├───────►│ PostgreSQL    │
│ Flutter (iOS/  │  REST │   Django + DRF             │        │ (Railway)     │
│ Android)       │       │   /api/v1/...              │        └───────────────┘
└───────────────┘        │   JWT auth, RBAC           │
        ▲                │   Celery workers + Redis   │        ┌───────────────┐
        │                └──────┬──────────┬──────────┘        │ Redis (queue  │
┌───────┴────────┐               │          │                   │ + cache)      │
│ App web         │               │          │                   └───────────────┘
│ authentifiée    │               │          │
│ (Flutter Web)   │               │          │           ┌────────────────────┐
│ dashboard/      │               │          └──────────►│ Stockage objet      │
│ lecteur cours   │               │                       │ S3-compatible       │
└─────────────────┘               │                       │ (PDF, images,       │
                                   │                       │ certificats, vidéo  │
                                   ▼                       │ MVP via URL signée) │
                        ┌─────────────────────┐            └────────────────────┘
                        │ Prestataire paiement │
                        │ (agrégateur Mobile   │            ┌────────────────────┐
                        │ Money Mali — à       │            │ Service email/SMS   │
                        │ contractualiser)     │            │ (Brevo/Sendgrid...) │
                        └─────────────────────┘            └────────────────────┘
```

### Décisions d'architecture et justifications

| Sujet | Décision proposée | Justification |
|---|---|---|
| Backend | **Django + Django REST Framework**, pas FastAPI | Le cahier des charges exige un back-office riche (admin, contenu, paiements, rapports) et du RBAC fin. Django apporte l'admin intégré (personnalisable, gain de temps énorme pour §32/§50), l'ORM + migrations, un écosystème mature (auth, permissions, stockage S3, JWT). FastAPI serait plus rapide en I/O pur mais obligerait à reconstruire admin/permissions/CMS à la main — non justifié ici. |
| Site public | **Next.js (React)**, pas Flutter Web | Le SEO est une exigence explicite (§38). Flutter Web rend via canvas/HTML peu lisible par les moteurs de recherche et charge un runtime lourd — mauvais pour des connexions limitées et le référencement. Next.js permet SSR/SSG, des pages légères et indexables. **C'est un écart à votre suggestion initiale ("Flutter Web ou technologie moderne adaptée") — à valider avec vous.** |
| App connectée (dashboard apprenant, lecteur de cours, formateur) | **Flutter**, partagé mobile + web | Pas de contrainte SEO ici (zone authentifiée), donc le codebase unique Flutter (mobile iOS/Android + Web) est justifié et réduit les coûts de double développement. |
| Admin (super admin/admin) | **Django Admin personnalisé pour le MVP**, dashboard dédié en V2 | Évite de construire un back-office complet dès le MVP alors que Django Admin, personnalisé (django-unfold ou équivalent), couvre déjà utilisateurs, formations, paiements manuels, coupons. |
| Base de données | **PostgreSQL** | Imposé par le cahier des charges, cohérent avec Railway. |
| Files/queue | **Celery + Redis** | Nécessaire pour : envoi d'emails, génération de PDF certificats, vérification asynchrone de statut de paiement, notifications, tâches IA. |
| Stockage fichiers | **Stockage objet compatible S3** (Cloudflare R2, Backblaze B2 ou AWS S3 — Railway n'a pas d'offre native, on branche un fournisseur externe via `django-storages`) | Le cahier des charges interdit de stocker les vidéos sur le serveur backend (§5, §15). |
| Vidéo | **MVP :** fichiers sur stockage objet + URL signées à expiration courte + vérification de possession de la formation. **V2 (si budget) :** service de streaming vidéo dédié (Bunny Stream, Cloudflare Stream ou Mux) pour un vrai streaming adaptatif et un token de lecture — protection nettement meilleure que des URL signées brutes. | Une URL signée reste un fichier téléchargeable pendant sa durée de validité : c'est un compromis honnête à MVP, pas une protection anti-piratage totale (voir §O, risques). |
| Paiement | Interface `PaymentProvider` abstraite + intégration d'un agrégateur adapté au Mali (CinetPay, PayDunya, Kkiapay ou FedaPay — tous supportent Mobile Money XOF). | **Nécessite vos identifiants marchand** : aucune intégration réelle ne peut être testée sans un contrat avec l'un de ces prestataires. Rien ne sera simulé comme "fonctionnel" sans identifiants réels (règle §53). |
| Hébergement | Railway (backend + PostgreSQL + Redis), conteneurisé (Dockerfile) pour rester portable vers un autre hébergeur. | Exigence §5/§45. |
| Monitoring/erreurs | Sentry (ou équivalent) + logs Django | Nécessaire pour la sécurité et le support en production. |

---

## C. Schéma de base de données (aperçu conceptuel)

*(Le DDL/migrations complets seront produits à l'étape de développement, pas ici.)*

| Domaine | Tables | Points clés |
|---|---|---|
| Comptes & rôles | `users`, `roles`, `permissions`, `user_roles`, `profiles` | `users` = identité + auth ; rôles multiples possibles par utilisateur (apprenant + formateur par ex.) ; `profiles` = pays, langue, téléphone, photo. |
| Catalogue | `categories`, `courses`, `course_categories`, `modules`, `lessons`, `lesson_resources` | `courses.status` = DRAFT/PENDING_REVIEW/PUBLISHED/ARCHIVED ; `lessons` référence vidéo (clé de stockage, pas URL publique) + durée + ordre. |
| Formateurs | `instructors`, `instructor_courses` | Un formateur ne peut modifier que ses propres formations (RBAC objet). |
| Progression | `enrollments`, `lesson_progress`, `course_progress` | `enrollments` = preuve d'accès (créée uniquement après paiement `paid` ou licence entreprise) ; progression calculée par leçons terminées. |
| Évaluation | `quizzes`, `questions`, `answers`, `quiz_attempts`, `quiz_results`, `exams`, `exam_attempts` | Score mini configurable par quiz/examen ; tentatives limitées ; ordre aléatoire des questions à l'examen. |
| Paiement | `payments`, `payment_transactions` | `payments.status` ∈ {pending, paid, failed, cancelled, refunded} ; `payment_transactions` = journal des appels au prestataire (idempotence, audit). |
| Certificats | `certificates`, `certificate_verifications` | Numéro unique (`SGT-{année}-{code_formation}-{séquence}`) ; `certificate_verifications` journalise les consultations publiques (anti-abus). |
| Entreprises (V2, schéma prêt dès le MVP) | `companies`, `company_users`, `company_licenses` | Licences achetées en lot, affectation aux employés, export résultats. |
| Marketing | `coupons`, `coupon_usages` | Pourcentage ou montant fixe, bornage dates/usages/formations. |
| Avis | `reviews` | Modération par statut (pending/approved/rejected). |
| Notifications | `notifications` | Canal (in-app/email/sms) + statut lu/non lu. |
| Abonnement (V2, schéma prêt dès le MVP) | `subscriptions` | Lien vers un plan (mensuel/annuel) et périmètre d'accès. |
| Parcours (V2) | `learning_paths`, `learning_path_courses` | Regroupement ordonné de formations. |
| IA (V2) | `ai_conversations`, `ai_messages` | Historique + contrôle de quota par utilisateur (anti-abus coût). |
| Système | `audit_logs`, `settings` | `audit_logs` = traçabilité actions sensibles (paiement validé manuellement, suppression, changement de rôle) ; `settings` = configuration éditable sans code (§50). |

Toutes les tables : `id` (UUID recommandé plutôt qu'auto-incrément pour éviter l'énumération), `created_at`, `updated_at`, `deleted_at` (soft delete) où pertinent (utilisateurs, formations, avis).

---

## D. Architecture frontend

**Site public (Next.js) :**
- Pages : accueil, catalogue (`/formations`), détail (`/formations/{slug}`), tarifs, contact, `/verify/{code}` (vérification certificat, publique, sans auth), CGU/confidentialité.
- Rendu SSR/SSG pour le SEO, données via l'API publique (endpoints non authentifiés).
- i18n prêt via `next-intl` (FR au lancement).

**Application Flutter (mobile + web authentifié) :**
- State management : **Riverpod** (recommandé, testable, sans BuildContext requis pour la logique).
- Navigation : **go_router**.
- Structure alignée sur votre proposition §39 (`core/models/services/providers/screens/widgets/routes`), détaillée en §K.
- Lecteur de cours : liste modules à gauche, lecteur vidéo au centre (`video_player` + URL signée à courte expiration), ressources/PDF sous la vidéo, boutons précédent/suivant/terminé.
- Design system : palette vert/blanc + gris foncé texte, cartes, badges, barres de progression — cohérent avec §4.

**Back-office (MVP → V2) :**
- MVP : Django Admin personnalisé (thème, listes filtrables, actions groupées type "valider ce paiement manuel").
- V2 : dashboard dédié avec graphiques (ventes, inscriptions, taux de réussite).

---

## E. Architecture backend

**Découpage en apps Django (bounded contexts) :**
`accounts`, `courses` (catalogue + modules/leçons), `learning` (progression), `assessments` (quiz + examens), `payments`, `certificates`, `companies`, `notifications`, `reviews`, `ai`, `common` (audit, settings, storage helpers).

- Settings scindés `base.py` / `dev.py` / `prod.py`, tout secret via variables d'environnement (`.env` en local, variables Railway en prod).
- Permissions DRF par rôle + vérifications objet (ex. un formateur ne peut modifier que ses propres formations — testé explicitement, cf. §40).
- Celery : envoi d'emails, génération PDF certificat, vérification asynchrone de statut de paiement auprès du prestataire, dispatch de notifications.

---

## F. Architecture API

- Base : `/api/v1/...`, JSON, pagination standard (page/page_size), format d'erreur homogène (`{"error": {"code", "message"}}`).
- Auth : JWT (accès courte durée + refresh token rotatif) via `djangorestframework-simplejwt`.
- Documentation : OpenAPI/Swagger générée automatiquement (`drf-spectacular`).
- Endpoints clés (extension de votre liste §31) : `auth/register`, `auth/login`, `auth/logout`, `auth/refresh`, `courses/`, `courses/{slug}/`, `courses/{id}/purchase`, `my-courses/`, `courses/{id}/progress`, `lessons/{id}/complete`, `quizzes/{id}/`, `quizzes/{id}/submit`, `exams/{id}/start`, `exams/{id}/submit`, `certificates/`, `certificates/{id}/`, `certificates/verify/{code}` (public), `payments/{id}/status`, `companies/{id}/employees`, `coupons/validate`.

---

## G. Architecture paiement

**Principe non négociable :** un paiement n'est jamais validé côté client. Le statut vient soit d'un **webhook signé du prestataire vérifié côté serveur**, soit d'une **vérification active de l'API du prestataire**, soit d'une **validation manuelle par un admin** (paiement manuel).

**Flux en ligne (agrégateur Mobile Money/carte) :**
1. Apprenant choisit une formation → backend crée `payment` (`pending`) + demande une transaction au prestataire.
2. Redirection/checkout côté prestataire.
3. Webhook du prestataire → backend vérifie la signature, puis **rappelle l'API du prestataire pour confirmer le statut réel** (jamais confiance aveugle au webhook seul).
4. Statut `paid` → création de `enrollment` → accès débloqué → notification.

**Flux paiement manuel :**
1. Apprenant choisit "paiement manuel" → instructions affichées → statut `pending`.
2. Apprenant saisit une référence (+ preuve optionnelle, upload contrôlé : type MIME, taille max).
3. Admin valide manuellement dans le back-office → statut `paid` → accès débloqué.

**Prestataires candidats Mali/XOF :** CinetPay, PayDunya, Kkiapay, FedaPay (tous agrègent Orange Money/Moov). **Aucun de ces choix n'est actionnable sans vos identifiants marchand** — à ce stade, l'architecture prévoit une interface `PaymentProvider` interchangeable, mais aucune intégration réelle ne peut être testée tant que le contrat n'est pas en place (règle §53).

---

## H. Architecture certificats

- Génération déclenchée à la réussite de l'examen final (score ≥ seuil configurable).
- Numéro unique : `SGT-{année}-{code_formation}-{séquence}` (contrainte d'unicité en base).
- PDF généré côté serveur (WeasyPrint ou ReportLab) avec logo, signature, QR code pointant vers `/verify/{code}`.
- Page publique `/verify/{code}` (Next.js, sans authentification) affichant statut VALIDE/INVALIDE, nom, formation, date, numéro — avec limitation de débit pour éviter l'énumération/scraping.

---

## I. Architecture sécurité

- Mots de passe : hachage Argon2/PBKDF2 (défaut Django, renforcé).
- RBAC : rôles + permissions en base + `permission_classes` DRF, vérifications au niveau objet.
- Rate limiting : sur l'authentification, la vérification de certificat, l'API en général (`django-ratelimit` / throttling DRF).
- CORS strict (whitelist des origines connues), CSRF sur les vues à cookies si utilisées.
- Upload : whitelist de types MIME, taille max, scan antivirus optionnel en V2.
- Secrets exclusivement en variables d'environnement, jamais commis en Git (`.env.example` fourni, `.env` dans `.gitignore`).
- HTTPS forcé, en-têtes de sécurité (HSTS, X-Content-Type-Options...).
- URL signées à expiration courte pour vidéos/certificats/preuves de paiement.
- `audit_logs` pour toute action sensible (validation paiement manuel, changement de rôle, suppression de compte).
- Sauvegardes PostgreSQL régulières (Railway backups ou `pg_dump` planifié).
- Droits des personnes : suppression de compte, export de données sur demande, politique de confidentialité/CGU publiées.

---

## J. Architecture application mobile (Flutter)

- Écrans conformes à votre liste §28 (16 écrans, SGT AI en V2).
- Offline-first : cache local (Hive ou Drift/SQLite) pour PDF téléchargés et file d'attente de progression ; synchronisation automatique au retour du réseau.
- **Limite honnête à annoncer :** aucune protection technique ne peut empêcher à 100% l'enregistrement d'écran sur un téléphone (limite matérielle/OS). L'architecture réduit le risque (pas d'URL permanente, expiration courte, pas de téléchargement direct des vidéos protégées) mais ne l'élimine pas — à ne jamais présenter comme une protection totale (règle §53).
- Notifications push : Firebase Cloud Messaging, prévu pour V2 (le MVP peut se limiter aux notifications in-app + email).
- Optimisation Android d'entrée de gamme : images compressées, listes paginées, vidéo en qualité adaptative si le service de streaming choisi le permet.

---

## K. Structure des dossiers proposée

```
sgt-academy/
├── docs/                          # documentation (ce document, guides à venir)
├── backend/
│   ├── config/                    # settings (base/dev/prod), urls, celery.py
│   ├── apps/
│   │   ├── accounts/
│   │   ├── courses/
│   │   ├── learning/              # progression
│   │   ├── assessments/           # quiz + examens
│   │   ├── payments/
│   │   ├── certificates/
│   │   ├── companies/
│   │   ├── notifications/
│   │   ├── reviews/
│   │   ├── ai/                    # V2
│   │   └── common/                # audit, settings, storage helpers
│   ├── requirements.txt
│   ├── manage.py
│   ├── Dockerfile
│   └── .env.example
├── frontend-web/                  # Next.js — site public SEO
│   ├── app/ (ou pages/)
│   ├── components/
│   └── package.json
└── mobile/                        # Flutter — app + web authentifié
    ├── lib/
    │   ├── core/
    │   ├── models/
    │   ├── services/
    │   ├── providers/
    │   ├── screens/
    │   ├── widgets/
    │   └── routes/
    └── pubspec.yaml
```

---

## L. Roadmap MVP → V2 → V3

| Phase | Contenu | Estimation |
|---|---|---|
| **MVP** | Accueil, inscription/connexion, catalogue, détail formation, achat, paiement (manuel + 1 agrégateur si identifiants disponibles), dashboard apprenant, lecteur vidéo/PDF, progression, quiz, examen final, certificat + vérification publique, administration (Django Admin personnalisé). | ~10-14 semaines (équipe réduite, voir §N) |
| **V2** | App mobile complète (parity), SGT AI (RAG), espace entreprise B2B, abonnements, parcours professionnels, mode hors ligne avancé, notifications multicanal (email/SMS/WhatsApp), dashboard admin dédié avec graphiques. | ~8-12 semaines supplémentaires |
| **V3** | Expansion multi-pays (Sénégal, Côte d'Ivoire...), multilingue (anglais), marketplace de parcours, gamification, éventuel live/webinaire, intégrations analytics avancées. | à cadrer selon traction commerciale |

---

## M. Liste des dépendances (indicative)

**Backend :** Django, djangorestframework, djangorestframework-simplejwt, drf-spectacular, psycopg2-binary, celery, redis, django-storages, boto3, django-cors-headers, django-filter, Pillow, weasyprint ou reportlab, qrcode, django-ratelimit, gunicorn, sentry-sdk, python-decouple (ou django-environ).

**Frontend web (Next.js) :** next, react, tailwindcss, next-intl, axios ou fetch natif, @tanstack/react-query.

**Mobile (Flutter) :** flutter_riverpod, go_router, dio, hive/drift, flutter_secure_storage, video_player, cached_network_image, easy_localization, firebase_messaging (V2).

**Infra :** PostgreSQL, Redis, stockage S3-compatible (R2/B2/S3), Railway, Docker.

---

## N. Estimation des ressources

**Équipe minimale suggérée :** 1 développeur backend (Django), 1 développeur frontend/Flutter (ou 2 si mobile + web en parallèle), 1 designer UI/UX à temps partiel, 1 chef de projet/QA (peut être partagé).

**Durée MVP :** environ 10 à 14 semaines à ce format d'équipe, hors délais d'obtention des identifiants prestataire de paiement (souvent le facteur bloquant réel).

**Coûts d'infrastructure (ordre de grandeur, à confirmer selon fournisseurs choisis) :** hébergement Railway (backend + PostgreSQL + Redis), stockage objet (facturé au Go stocké + bande passante sortante), éventuel service de streaming vidéo dédié (facturé aux minutes visionnées), service email transactionnel, nom de domaine. Ces montants dépendent du volume réel d'apprenants et ne peuvent pas être garantis sans devis fournisseurs — je ne présenterai jamais un chiffre précis comme définitif sans devis réel (règle §53).

---

## O. Risques techniques (et décisions ouvertes)

| Risque | Impact | Mitigation |
|---|---|---|
| Vidéo copiable malgré URL signées | Perte de contenu premium | Expiration courte, vérification de possession à chaque lecture, envisager un service de streaming dédié dès que le budget le permet (V2) |
| Intégration paiement dépend d'un contrat externe | Bloque le MVP marchand tant que non signé | Prévoir le paiement manuel comme solution de lancement immédiat, indépendante d'un prestataire |
| Connectivité limitée au Mali | Abandon utilisateurs si pages lentes | Next.js SSR, images optimisées, vidéo adaptative, pagination systématique |
| Abus de l'IA (coût) | Facture IA incontrôlée | Quotas par utilisateur, cache des réponses fréquentes, RAG limité aux contenus SGT (V2, hors MVP) |
| Fraude sur preuve de paiement manuel | Accès frauduleux à une formation | Validation humaine obligatoire + journal d'audit + limitation des tentatives |
| Fraude certificat | Atteinte à la crédibilité de la certification | Numéro unique contraint en base + page de vérification publique avec limitation de débit |
| Synchronisation hors-ligne mobile | Conflits de progression | Résolution par horodatage serveur faisant autorité, file de synchronisation idempotente |
| Portabilité hors Railway | Dépendance à un hébergeur | Conteneurisation Docker dès le départ |

**Décisions à valider avec vous avant de coder :**
1. Confirmez-vous **Next.js pour le site public** (SEO) plutôt que Flutter Web, avec Flutter réservé à l'espace connecté + mobile ?
2. Quel **agrégateur de paiement** Mali souhaitez-vous contractualiser en premier (CinetPay, PayDunya, Kkiapay, FedaPay, autre) ? Sans réponse, le MVP démarrera avec le **paiement manuel uniquement**, ce qui est suffisant pour lancer commercialement.
3. Budget prévu pour un **service de streaming vidéo dédié** (Bunny/Cloudflare Stream/Mux), ou stockage S3 + URL signées suffisant pour le MVP ?

---

## Prochaine étape

En attente de votre validation. Une fois validée, la première étape de développement proposée sera : squelette du projet Django (apps, modèles du schéma §C, migrations initiales, configuration `.env`), sans front ni paiement réel, testable en local avec un superuser — conformément à la méthode de travail §42 (pas de génération massive de fichiers en une fois).
