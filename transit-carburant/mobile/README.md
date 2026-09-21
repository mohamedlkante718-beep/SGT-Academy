# TransitCarburant — Application mobile (Flutter)

Application utilisée par les agents (frontière, dépôt) et le
superviseur, sur la base des maquettes de conception. Voir
`docs/CAHIER-DES-CHARGES.md` et `docs/DB-SCHEMA.md` à la racine du
projet pour le contexte complet.

> **Validé** avec Flutter 3.47.5 (stable) : `flutter analyze` ne
> remonte aucun problème et `flutter test` passe (6/6, dans
> `test/crypto_and_manifeste_test.dart`), y compris un test de
> régression pour un vrai piège d'interopérabilité trouvé pendant
> cette validation (voir encadré ci-dessous). Ça ne remplace pas un
> test sur un appareil réel : lance quand même `flutter run` avant la
> mise en production.

> **Bug trouvé et corrigé pendant la validation** : le format de date
> produit par `DateTime.toUtc().toIso8601String()` en Dart
> (`2026-01-02T03:04:05.000Z`) diffère de celui que `datetime.isoformat()`
> produit en Python pour la même date (`2026-01-02T03:04:05+00:00`).
> Le backend reconstruisait ce texte à partir d'un objet `datetime`
> reformaté au lieu de garder la chaîne brute du client, ce qui aurait
> fait échouer la vérification de signature pour **tous** les
> manifestes envoyés par un vrai téléphone. Corrigé côté backend
> (`ManifesteIn.date_creation` est maintenant une chaîne opaque,
> jamais reformatée avant la vérification — voir
> `docs/DB-SCHEMA.md` § "Piège d'interopérabilité") et couvert par un
> test de non-régression des deux côtés.

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
