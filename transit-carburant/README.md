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
├── docs/       # cahier des charges, schéma de base de données, déploiement
├── backend/    # API centrale FastAPI (Python) — testée, fonctionnelle
└── mobile/     # application Flutter (agents + supervision) — analysée et testée (flutter analyze/test)
```

## Démarrer

1. Lire `docs/CAHIER-DES-CHARGES.md` pour le contexte fonctionnel.
2. Lancer le backend : voir `backend/README.md`.
3. Lancer l'application mobile : voir `mobile/README.md`.
4. Déployer le backend en ligne : voir `docs/DEPLOIEMENT.md`.

## État actuel

- Backend : auth, gestion des postes avec génération de clés Ed25519,
  synchronisation idempotente des manifestes et des contrôles, upload
  de la photo d'un manifeste, tableau de bord — couvert par des tests
  qui passent, chacun sur sa propre base isolée (`8 passed`), plus un
  test dédié qui rejoue tout le parcours sur une vraie base PostgreSQL
  (pas seulement SQLite) — validé avec un PostgreSQL 16 réel installé
  dans l'environnement de développement.
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
- Déploiement : marche à suivre complète dans `docs/DEPLOIEMENT.md`
  (Render + base PostgreSQL gratuite externe). L'image Docker fournie
  (`backend/Dockerfile`, `docker-compose.yml`) n'a pas pu être
  construite dans cet environnement de développement, dont la
  politique réseau bloque l'accès au CDN de Docker Hub — sans rapport
  avec les serveurs de Render, qui construisent ailleurs.
- Trois bugs réels trouvés et corrigés en validant ce projet avec de
  vrais outils plutôt qu'en se fiant à la relecture : un piège de
  format de date entre Dart et Python qui aurait fait échouer toute
  vérification de signature, une fuite du chemin photo local (sans
  signification hors de l'appareil) dans les données synchronisées, et
  un test censé valider PostgreSQL qui validait silencieusement la
  mauvaise base de données — voir `docs/DB-SCHEMA.md` et
  `backend/tests/test_postgres_compat.py`.
