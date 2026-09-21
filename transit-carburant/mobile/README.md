# TransitCarburant — Application mobile (Flutter)

Application utilisée par les agents (frontière, dépôt) et le
superviseur, sur la base des maquettes de conception. Voir
`docs/CAHIER-DES-CHARGES.md` et `docs/DB-SCHEMA.md` à la racine du
projet pour le contexte complet.

> **Important** : cet environnement de développement ne dispose pas du
> SDK Flutter/Dart. Ce code a été écrit avec soin (schéma SQLite,
> logique de signature/vérification Ed25519 identique au backend,
> écrans conformes aux maquettes) mais **n'a pas pu être compilé ni
> testé ici**. Avant de t'y fier, lance au minimum :
>
> ```bash
> flutter pub get
> flutter analyze
> flutter test
> ```
>
> et corrige les éventuelles erreurs de version d'API que `flutter
> analyze` remonterait (les packages tiers changent parfois leur API
> d'une version à l'autre).

## Ce qui est fonctionnel dans ce squelette

- Base SQLite locale (`sqflite`) : postes, manifestes, contrôles
  dépôt, avec un statut de synchronisation par enregistrement.
- Signature et vérification Ed25519 hors ligne (`package:cryptography`),
  avec un algorithme de contenu canonique **identique** à celui du
  backend (`build_manifeste_payload` / `Manifeste.canonicalPayload()`).
- Les 6 écrans des maquettes : connexion, nouveau contrôle (frontière),
  manifeste QR (frontière, généré avec `qr_flutter`), scanner (dépôt),
  vérification (dépôt), tableau de bord (superviseur).
- Synchronisation différée, idempotente, silencieuse en cas d'échec
  réseau (`SyncService`).
- Stockage sécurisé de la clé privée de signature d'un poste
  (`flutter_secure_storage`, jamais en clair, jamais envoyée au
  serveur).

## Ce qui reste à faire

- **Scan QR par caméra** : l'écran dépôt a une saisie manuelle
  pleinement fonctionnelle, mais la lecture caméra n'est pas câblée
  (à intégrer avec un package comme `mobile_scanner` — son API change
  assez souvent d'une version à l'autre pour qu'il vaille mieux la
  câbler avec la version réellement choisie plutôt que de deviner ici).
- **Prise de photo de la citerne/du scellé** (`image_picker` ou
  équivalent) : le champ `photo_path` existe déjà dans le modèle.
- Écran d'historique des contrôles (frontière et dépôt).
- Synchronisation en arrière-plan périodique (aujourd'hui déclenchée
  après chaque création/contrôle, mais pas de tâche planifiée).

## Installation

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://<ip-du-backend>:8000
```

Par défaut, `API_BASE_URL` vaut `http://10.0.2.2:8000` (accès au
`localhost` de la machine hôte depuis l'émulateur Android).

## Provisionnement d'un poste frontière

1. Un administrateur crée le poste via l'API (`POST /postes`,
   `type: "frontiere"`) : le backend génère une paire de clés Ed25519
   et renvoie la clé privée **une seule fois**.
2. Sur l'appareil de l'agent affecté à ce poste, ouvrir "Provisionner
   une clé de poste (admin)" depuis l'écran de connexion, et y coller
   l'identifiant du poste et la clé privée.
3. L'agent peut ensuite se connecter normalement : chaque manifeste
   qu'il crée est signé avec cette clé, vérifiable hors ligne au
   dépôt avec la clé publique du poste (synchronisée automatiquement).
