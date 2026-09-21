# TransitCarburant — Cahier des charges (MVP)

## 1. Contexte et objectif

Au Mali, les citernes de carburant et de gaz transitant de la frontière vers les
dépôts sont contrôlées manuellement, camion par camion, sur papier, au niveau du
dépôt. Cette saisie répétitive bloque la route d'accès au dépôt le temps du
traitement de chaque véhicule.

**Objectif** : déplacer la saisie des données du camion vers le poste frontière
(temps mort du trajet exploité), et permettre au dépôt de valider un camion en
quelques secondes par un simple scan, vérifiable même sans connexion Internet.

## 2. Acteurs et rôles

| Rôle | Poste | Droits |
|---|---|---|
| Agent frontière | Poste frontière | Créer un contrôle, générer un manifeste signé (QR) |
| Agent dépôt | Dépôt | Scanner un manifeste, vérifier, valider ou signaler une anomalie |
| Superviseur | Douane / société pétrolière | Consulter le tableau de bord, les alertes, les rapports |
| Administrateur | — | Gérer les comptes, les postes, les transporteurs, les clés de signature |

## 3. Périmètre du MVP

### Inclus
- Enregistrement d'un camion au poste frontière (formulaire + photo + génération
  d'un manifeste numérique signé, encodé en QR code)
- Le manifeste QR est **auto-vérifiable hors connexion** (signature numérique
  embarquée, clé publique du poste préchargée sur les appareils dépôt)
- Vérification et validation/rejet au dépôt (scan + checklist physique)
- Synchronisation différée vers un serveur central dès que le réseau est
  disponible (aucune fonction critique n'attend le réseau)
- Tableau de bord de supervision (camions en transit, alertes, volumes)
- Journal d'audit immuable de tous les contrôles

### Explicitement hors périmètre (retiré du MVP, non planifié pour l'instant)
- Géolocalisation / suivi en temps réel du camion sur la route
- File d'attente / créneaux horaires automatisés au dépôt
- Application dédiée aux transporteurs
- Notifications SMS automatiques
- Multi-pays / autres corridors

## 4. Hypothèses de travail retenues

- Un seul corridor pilote : poste frontière de Kourémalé → dépôt de Bamako
  (extensible ensuite à d'autres postes)
- Une clé de signature par poste frontière, générée à la création du poste par
  l'administrateur, stockée chiffrée sur l'appareil de l'agent affecté
- Comptes utilisateurs créés manuellement par un administrateur (pas
  d'auto-inscription)
- Backend central minimal : uniquement pour agréger les manifestes/alertes pour
  le tableau de bord et distribuer les clés publiques des postes — jamais un
  passage obligé pour créer ou vérifier un manifeste

## 5. Exigences fonctionnelles

- **FR-1** : L'agent frontière crée une fiche camion complète hors ligne
  (plaque, transporteur, chauffeur, cargaison, quantité, n° de scellé, photo,
  dépôt de destination).
- **FR-2** : Le système signe numériquement le manifeste avec la clé du poste et
  l'encode dans un QR code affiché/imprimable.
- **FR-3** : L'agent dépôt scanne le QR ; l'application vérifie la signature
  localement, sans réseau, et affiche le manifeste si elle est valide.
- **FR-4** : L'agent dépôt confirme une checklist physique (scellé intact,
  quantité conforme) et valide l'entrée ou signale une anomalie.
- **FR-5** : Toute anomalie (scellé cassé, écart de quantité, camion non
  attendu, signature invalide) génère une alerte remontée au superviseur dès la
  synchronisation.
- **FR-6** : Le superviseur visualise les camions en transit, leur statut, et
  les alertes actives sur un tableau de bord.
- **FR-7** : Chaque téléphone conserve ses données localement (SQLite) et les
  synchronise dès qu'une connexion est disponible, sans perte ni doublon.

## 6. Exigences non fonctionnelles

- **Offline-first strict** : créer un manifeste et le vérifier ne dépendent
  jamais du réseau.
- **Intégrité** : un manifeste validé n'est plus modifiable (write-once) ; tout
  changement d'état est journalisé (audit log append-only).
- **Faible consommation de données** : synchronisation incrémentale (deltas
  uniquement), déclenchée manuellement ou automatiquement selon le réglage de
  l'utilisateur.
- **Compatibilité matérielle** : Android 8+ (API 26+), fonctionnement correct
  sur smartphones d'entrée/milieu de gamme.
- **Sécurité** : mots de passe hashés, communications chiffrées (HTTPS) lors de
  la synchronisation, clés privées jamais transmises au serveur.

## 7. Architecture technique retenue

- **Mobile (agents + tableau de bord superviseur)** : Flutter — un seul code
  source pour Android et le web (dashboard superviseur en Flutter Web).
- **Stockage local** : SQLite (`sqflite`).
- **Signature/vérification** : cryptographie asymétrique (Ed25519), vérifiable
  hors ligne avec la clé publique du poste préchargée.
- **Backend central** : FastAPI + PostgreSQL (SQLite en développement),
  hébergeable gratuitement au démarrage (Render/Fly.io, tiers gratuits).
- **Synchronisation** : API REST, endpoints d'envoi par lot (batch upload) et de
  téléchargement des clés publiques des postes.

## 8. MVP — livrables

1. Application Flutter : écrans Connexion, Nouveau contrôle (frontière),
   Manifeste QR (frontière), Scanner (dépôt), Vérification (dépôt), Tableau de
   bord (superviseur, Flutter Web).
2. Backend FastAPI : modèles de données, endpoints de synchronisation,
   distribution des clés publiques.
3. Base de données locale et serveur (voir `DB-SCHEMA.md`).
4. Documentation d'installation et guide de test du corridor pilote.
