# TransitCarburant — Schéma de base de données

Les mêmes entités existent en local (SQLite, sur chaque téléphone) et sur le
serveur central (PostgreSQL). Le champ `sync_status` n'existe que côté local.

## users
| Champ | Type | Note |
|---|---|---|
| id | uuid (PK) | |
| matricule | text (unique) | |
| nom_complet | text | |
| role | enum | agent_frontiere \| agent_depot \| superviseur \| admin |
| poste_id | uuid (FK -> postes) | |
| password_hash | text | |
| actif | bool | |
| created_at | datetime | |

## postes
| Champ | Type | Note |
|---|---|---|
| id | uuid (PK) | |
| nom | text | ex. "Kourémalé" |
| type | enum | frontiere \| depot |
| ville | text | |
| gps_lat, gps_lng | float | |
| cle_publique | text | clé publique Ed25519 du poste (frontière uniquement) |

## transporteurs
| Champ | Type |
|---|---|
| id | uuid (PK) |
| nom_societe | text |
| telephone | text |
| numero_agrement | text |

## chauffeurs
| Champ | Type |
|---|---|
| id | uuid (PK) |
| nom_complet | text |
| numero_piece_identite | text |
| telephone | text |

## vehicules
| Champ | Type |
|---|---|
| id | uuid (PK) |
| plaque_immatriculation | text (unique) |
| type_citerne | text |
| capacite_max | float |

## manifestes
| Champ | Type | Note |
|---|---|---|
| id | uuid (PK) | généré localement à la création |
| vehicule_id | uuid (FK) | |
| transporteur_id | uuid (FK) | |
| chauffeur_id | uuid (FK) | |
| poste_frontiere_id | uuid (FK -> postes) | |
| depot_destination_id | uuid (FK -> postes) | |
| type_cargaison | enum | essence \| gasoil \| gaz_butane |
| quantite_declaree | float | |
| unite | enum | litres \| kg |
| numero_scelle | text | |
| photo_path | text | chemin local, uploadé lors de la sync |
| agent_frontiere_id | uuid (FK -> users) | |
| signature_numerique | text | signature Ed25519 (base64) du contenu du manifeste |
| date_creation | datetime | |
| statut | enum | genere \| en_route \| controle_depot \| valide \| anomalie |
| sync_status (local uniquement) | enum | local_only \| synced \| conflict |

## controles_depot
| Champ | Type |
|---|---|
| id | uuid (PK) |
| manifeste_id | uuid (FK) |
| agent_depot_id | uuid (FK -> users) |
| scelle_intact | bool |
| quantite_conforme | bool |
| remarque | text |
| resultat | enum: valide \| anomalie |
| date_controle | datetime |
| sync_status (local uniquement) | enum |

## alertes
| Champ | Type |
|---|---|
| id | uuid (PK) |
| manifeste_id | uuid (FK, nullable) |
| type | enum: scelle_casse \| ecart_quantite \| camion_non_attendu \| signature_invalide \| autre |
| gravite | enum: haute \| moyenne \| basse |
| description | text |
| statut | enum: ouverte \| traitee |
| date_creation | datetime |

## audit_log
| Champ | Type |
|---|---|
| id | uuid (PK) |
| user_id | uuid (FK) |
| action | text |
| entite, entite_id | text |
| date | datetime |
| details | json |

## sync_log (serveur uniquement)
| Champ | Type | Note |
|---|---|---|
| id | uuid (PK) | |
| entite | text | nom de la table synchronisée |
| entite_id | uuid | |
| device_id | text | identifiant de l'appareil source |
| date_sync | datetime | |
| statut | enum: ok \| conflit | |

## Principe anti-doublon / anti-conflit

Chaque enregistrement créé localement porte un `id` (UUID v4) généré sur
l'appareil au moment de la création. La synchronisation envoie cet id au
serveur, qui l'utilise comme clé primaire (upsert idempotent) : renvoyer deux
fois le même manifeste ne crée jamais de doublon. Un `manifeste` ne peut être
modifié après son premier `controles_depot` associé (write-once) ; toute
correction ultérieure passe par une nouvelle entrée dans `audit_log`, jamais
par une mise à jour silencieuse.
