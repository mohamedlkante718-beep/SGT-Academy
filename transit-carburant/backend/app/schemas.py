from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

UUID_PATTERN = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

from app.models import (
    AlerteGraviteEnum,
    AlerteStatutEnum,
    AlerteTypeEnum,
    CargaisonEnum,
    ControleResultatEnum,
    ManifesteStatutEnum,
    PosteTypeEnum,
    RoleEnum,
    UniteEnum,
)


# --- Auth ---


class LoginRequest(BaseModel):
    matricule: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: RoleEnum
    poste_id: str | None = None


# --- Postes ---


class PosteCreate(BaseModel):
    nom: str
    type: PosteTypeEnum
    ville: str
    gps_lat: float | None = None
    gps_lng: float | None = None


class PosteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nom: str
    type: PosteTypeEnum
    ville: str
    gps_lat: float | None
    gps_lng: float | None
    cle_publique: str | None


class PosteCreated(BaseModel):
    poste: PosteOut
    cle_privee_a_provisionner: str


# --- Users ---


class UserCreate(BaseModel):
    matricule: str
    nom_complet: str
    role: RoleEnum
    poste_id: str | None = None
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matricule: str
    nom_complet: str
    role: RoleEnum
    poste_id: str | None
    actif: bool


# --- Sync : manifestes ---


class ManifesteIn(BaseModel):
    """Manifeste tel qu'envoyé par l'appli mobile lors de la synchronisation.

    Les entités (véhicule, transporteur, chauffeur) sont envoyées sous
    forme dénormalisée : le serveur les résout ou les crée par clé
    naturelle (idempotent), sans jamais dépendre d'un identifiant
    serveur inconnu du téléphone au moment de la création hors ligne.
    """

    id: str = Field(pattern=UUID_PATTERN)
    plaque_immatriculation: str
    type_citerne: str | None = None
    transporteur_nom: str
    transporteur_telephone: str | None = None
    chauffeur_nom: str
    chauffeur_piece_identite: str
    chauffeur_telephone: str | None = None
    poste_frontiere_id: str
    depot_destination_id: str
    type_cargaison: CargaisonEnum
    quantite_declaree: float
    unite: UniteEnum
    numero_scelle: str
    photo_path: str | None = None
    agent_frontiere_id: str
    signature_numerique: str
    # Chaîne brute, telle qu'émise par l'appareil qui a signé le
    # manifeste (ex. `DateTime.toUtc().toIso8601String()` côté Dart) :
    # gardée verbatim, jamais reformatée, car c'est cet exact texte qui
    # entre dans le contenu signé (voir build_manifeste_payload). La
    # reformater via un objet datetime romprait la vérification de
    # signature (Python et Dart ne sérialisent pas un datetime UTC de
    # façon identique : `+00:00` vs `Z`, précision des millisecondes).
    date_creation: str


class ManifesteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vehicule_id: str
    transporteur_id: str
    chauffeur_id: str
    poste_frontiere_id: str
    depot_destination_id: str
    type_cargaison: CargaisonEnum
    quantite_declaree: float
    unite: UniteEnum
    numero_scelle: str
    agent_frontiere_id: str
    signature_valide: bool
    date_creation: datetime
    statut: ManifesteStatutEnum


class ManifesteSyncResult(BaseModel):
    id: str
    signature_valide: bool
    statut: ManifesteStatutEnum


class ManifesteBatchIn(BaseModel):
    manifestes: list[ManifesteIn]


class ManifesteBatchOut(BaseModel):
    resultats: list[ManifesteSyncResult]


class ManifestePhotoOut(BaseModel):
    manifeste_id: str
    photo_path: str


# --- Sync : contrôles dépôt ---


class ControleDepotIn(BaseModel):
    id: str
    manifeste_id: str
    agent_depot_id: str
    scelle_intact: bool
    quantite_conforme: bool
    remarque: str | None = None
    resultat: ControleResultatEnum
    date_controle: datetime


class ControleBatchIn(BaseModel):
    controles: list[ControleDepotIn]


class ControleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    manifeste_id: str
    resultat: ControleResultatEnum


class ControleBatchOut(BaseModel):
    resultats: list[ControleOut]


# --- Alertes ---


class AlerteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    manifeste_id: str | None
    type: AlerteTypeEnum
    gravite: AlerteGraviteEnum
    description: str
    statut: AlerteStatutEnum
    date_creation: datetime


# --- Dashboard ---


class DashboardSummary(BaseModel):
    camions_en_transit: int
    camions_au_depot_aujourdhui: int
    alertes_actives: int
    volume_total_aujourdhui: float
