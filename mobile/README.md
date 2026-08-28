# SGT Academy — Application (Flutter)

L'espace connecté de l'apprenant : connexion, tableau de bord (« Mes formations »), programme d'une formation avec progression, certificats. Voir [`../docs/01-ANALYSE-ARCHITECTURE.md`](../docs/01-ANALYSE-ARCHITECTURE.md) pour le choix de Flutter ici (pas d'enjeu SEO, contrairement au site public en Next.js).

Cible actuelle : **web** (pour tester sans rien installer sur téléphone). Android/iOS viendront ensuite à partir du même code.

## Écrans disponibles

| Écran | Contenu |
|---|---|
| Connexion | Email/mot de passe (JWT) |
| Inscription | Création de compte |
| Tableau de bord | Mes formations avec barre de progression, onglet Certificats |
| Programme de la formation | Modules/leçons, statut, bouton « Terminer » qui met à jour la progression en direct |

## Ce qui n'est pas encore réel

- **Pas de lecteur vidéo** : le backend n'expose pas encore d'URL signée pour le streaming (prévu, voir §15 de l'architecture) — l'écran affiche le programme et permet de marquer une leçon terminée, sans lire de vidéo.
- Onboarding, notifications push, mode hors-ligne, quiz/examen : pas encore construits côté app (l'API existe côté backend).
- Stocke le token JWT via `shared_preferences` (équivalent web du localStorage) — à revoir en V2 pour plus de robustesse.

## Installation locale (Windows, étape par étape)

1. **Installer Flutter** : suivez [docs.flutter.dev/get-started/install/windows](https://docs.flutter.dev/get-started/install/windows) (inclut Dart, pas besoin de l'installer séparément). Vérifiez avec `flutter doctor`.
2. **Cloner le dépôt** (si ce n'est pas déjà fait) :
   ```
   git clone https://github.com/mohamedlkante718-beep/sgt-academy.git
   cd sgt-academy/mobile
   ```
3. **Installer les dépendances** :
   ```
   flutter pub get
   ```
4. **Démarrer le backend** d'abord (voir `../backend/README.md`), sur `http://127.0.0.1:8000`.
5. **Lancer l'app dans Chrome** :
   ```
   flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
   ```
6. **Tester** : créez un compte ou connectez-vous, achetez une formation depuis le site public, puis retrouvez-la dans l'app.

Pour pointer vers un backend déployé (Railway), remplacez `API_BASE_URL` par son adresse, ex :
```
flutter run -d chrome --dart-define=API_BASE_URL=https://votre-domaine.up.railway.app/api/v1
```

## Erreurs possibles

- **Écran blanc au chargement** → ouvrez la console du navigateur. Si vous voyez une erreur liée à `canvaskit`/`gstatic.com`, votre réseau bloque ce CDN (pare-feu d'entreprise) ; relancez avec `--web-renderer html`.
- **« Impossible de charger vos formations »** → le backend n'est pas démarré, ou `API_BASE_URL` ne correspond pas à son adresse réelle.

## Déploiement sur Railway (pour avoir un vrai lien, sans rien installer)

Le dossier `dist/` contient une version déjà compilée de l'app (web), servie par un petit serveur nginx via `Dockerfile`. C'est un **instantané** : il ne se reconstruit pas tout seul à chaque changement de code — voir la note en bas.

1. Sur le tableau de bord Railway, dans le **même projet** que le backend (`SGT-Academy` + `Postgres`), cliquez sur **« + New »** → **« GitHub Repo »** → choisissez à nouveau `SGT-Academy`. Un nouveau service est créé.
2. Sur ce nouveau service → **Settings** → **Root Directory** : entrez `mobile`.
3. Toujours dans **Settings** → **Networking** → **« Generate Domain »**. Utilisez **le port `80`** cette fois (c'est le port sur lequel nginx écoute).
4. Attendez le déploiement (icône verte). Ouvrez l'adresse générée — l'application s'affiche directement, plus besoin d'installer quoi que ce soit.

**Important — ceci est un instantané, pas du direct** : si le code de l'app change ensuite, il faut regénérer `dist/` (`flutter build web --dart-define=API_BASE_URL=...`) et pousser à nouveau sur GitHub pour que ce service se mette à jour. Demandez-le si besoin, la commande est rapide à relancer.

## Prochaine étape

Lecteur vidéo (une fois le stockage protégé branché côté backend), quiz/examen, puis build Android/iOS réels.
