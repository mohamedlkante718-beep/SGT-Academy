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
└── mobile/     # application Flutter (agents + supervision) — non compilée ici, voir mobile/README.md
```

## Démarrer

1. Lire `docs/CAHIER-DES-CHARGES.md` pour le contexte fonctionnel.
2. Lancer le backend : voir `backend/README.md`.
3. Lancer l'application mobile : voir `mobile/README.md`.

## État actuel

- Backend : scaffolding complet (auth, gestion des postes avec
  génération de clés Ed25519, synchronisation idempotente des
  manifestes et des contrôles, tableau de bord), couvert par des
  tests qui passent (`3 passed`).
- Mobile : écrans, base SQLite locale et logique de signature/
  vérification écrits en suivant les maquettes, mais **non compilés
  ni testés** faute de SDK Flutter dans cet environnement de
  développement — à valider avec `flutter analyze` / `flutter test`
  avant la première exécution réelle.
