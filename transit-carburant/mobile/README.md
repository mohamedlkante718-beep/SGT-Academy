# TransitCarburant — Application mobile (Flutter)

Application utilisée par les agents (frontière, dépôt) et le
superviseur, sur la base des maquettes de conception. Voir
`docs/CAHIER-DES-CHARGES.md` et `docs/DB-SCHEMA.md` à la racine du
projet pour le contexte complet.

> **Validé** avec Flutter 3.47.5 (stable) : `flutter analyze` ne
> remonte aucun problème et `flutter test` passe (8/8, dans
> `test/crypto_and_manifeste_test.dart`), y compris un test de
> régression pour un vrai piège d'interopérabilité trouvé pendant
> cette validation (voir encadré ci-dessous). Les dossiers `android/`
> et `ios/` ont été générés (`flutter create`) avec les permissions
> caméra nécessaires au scan QR. **Limite de cet environnement** :
> pas de SDK Android ni d'Xcode disponibles ici, donc `flutter build
> apk` / `flutter run` sur un appareil réel n'ont pas pu être testés
> — à faire avant la mise en production.

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
- Les 6 écrans des maquettes : connexion, nouveau contrôle (frontière,
  avec prise de photo de la citerne/du scellé via `image_picker` —
  caméra uniquement, jamais la galerie, pour que la photo soit bien
  celle prise sur place), manifeste QR (frontière, généré avec
  `qr_flutter`), scanner (dépôt, caméra réelle via `mobile_scanner` +
  saisie manuelle de secours), vérification (dépôt), tableau de bord
  (superviseur).
- Écrans d'historique local (frontière : manifestes créés sur cet
  appareil ; dépôt : contrôles effectués), accessibles depuis une
  barre de navigation en bas de l'écran principal de chaque rôle.
- Déconnexion disponible sur les trois écrans (frontière, dépôt,
  superviseur) — absente jusqu'ici.
- Synchronisation différée, idempotente, silencieuse en cas d'échec
  réseau (`SyncService`), y compris l'envoi du fichier photo lui-même
  (pas seulement son chemin local) une fois le manifeste déjà
  synchronisé — voir `docs/DB-SCHEMA.md` § "Envoi de la photo...".
- Stockage sécurisé de la clé privée de signature d'un poste
  (`flutter_secure_storage`, jamais en clair, jamais envoyée au
  serveur).
- Icône d'application et écran de démarrage aux couleurs de la marque
  (bouclier-goutte navy/teal — voir `assets/icon/`), générés avec
  `flutter_launcher_icons` et `flutter_native_splash` à partir des
  sources dans `assets/icon/app_icon.png` (icône pleine, fond navy) et
  `app_icon_foreground.png` (glyphe seul, transparent — couche
  adaptative Android et image de démarrage).

## Ce qui reste à faire

- Synchronisation en arrière-plan périodique (aujourd'hui déclenchée
  après chaque création/contrôle, mais pas de tâche planifiée).
- Test sur un appareil Android réel (permission caméra, autonomie,
  écran d'entrée de gamme) — voir la limite de cet environnement
  ci-dessus.

## Installation

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://<ip-du-backend>:8000
```

Par défaut, `API_BASE_URL` vaut `http://10.0.2.2:8000` (accès au
`localhost` de la machine hôte depuis l'émulateur Android).

## Identité visuelle

Pour régénérer les icônes/l'écran de démarrage après une modification
des fichiers sous `assets/icon/` :

```bash
dart run flutter_launcher_icons
dart run flutter_native_splash:create
```

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
