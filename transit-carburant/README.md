# TransitCarburant

Contrôle numérique des citernes de carburant et de gaz, de la
frontière au dépôt — pour éliminer le blocage des routes causé par
l'enregistrement manuel, camion par camion, sur papier.

> Projet distinct de la plateforme e-learning Safe Green Tech
> (dossiers `backend/`, `frontend-web/`, `mobile/` à la racine du
> dépôt) : voir ce dossier `transit-carburant/` pour tout ce qui
> concerne ce produit.

## Structure

```
transit-carburant/
├── docs/       # cahier des charges, schéma de base de données
├── backend/    # API centrale FastAPI (Python) — testée, fonctionnelle
└── mobile/     # application Flutter (agents + supervision) — analysée et testée (flutter analyze/test)
```

## Démarrer

1. Lire `docs/CAHIER-DES-CHARGES.md` pour le contexte fonctionnel.
2. Lancer le backend : voir `backend/README.md`.
3. Lancer l'application mobile : voir `mobile/README.md`.

## État actuel

- Backend : auth, gestion des postes avec génération de clés Ed25519,
  synchronisation idempotente des manifestes et des contrôles, upload
  de la photo d'un manifeste, tableau de bord — couvert par des tests
  qui passent, chacun sur sa propre base isolée (`8 passed`).
- Mobile : écrans complets (dont photo de la citerne/du scellé à la
  frontière — envoyée au serveur après la synchro des données, pas
  seulement son chemin local — scan QR par caméra au dépôt avec
  `mobile_scanner`, saisie manuelle de secours, historiques locaux,
  déconnexion), base SQLite locale, logique de signature/vérification,
  le tout suivant les maquettes et validé avec un vrai SDK Flutter
  (3.47.5 stable) : `flutter analyze` propre, `flutter test` passe
  (`8 passed`). Les dossiers `android/`/`ios/` sont générés avec les
  permissions caméra nécessaires. Non testé faute de SDK Android/Xcode
  ici : la compilation/exécution réelle sur appareil. Reste à faire :
  synchronisation en arrière-plan, icône d'app, stockage persistant des
  photos en production — voir `mobile/README.md` et `backend/README.md`.
- Deux bugs réels trouvés et corrigés pendant cette validation croisée
  Dart/Python — un piège de format de date qui aurait fait échouer
  toute vérification de signature, et une fuite du chemin photo local
  (sans signification hors de l'appareil) dans les données
  synchronisées — voir `docs/DB-SCHEMA.md`.
