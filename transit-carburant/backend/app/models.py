import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RoleEnum(str, enum.Enum):
    agent_frontiere = "agent_frontiere"
    agent_depot = "agent_depot"
    superviseur = "superviseur"
    admin = "admin"


class PosteTypeEnum(str, enum.Enum):
    frontiere = "frontiere"
    depot = "depot"


class CargaisonEnum(str, enum.Enum):
    essence = "essence"
    gasoil = "gasoil"
    gaz_butane = "gaz_butane"


class UniteEnum(str, enum.Enum):
    litres = "litres"
    kg = "kg"


class ManifesteStatutEnum(str, enum.Enum):
    genere = "genere"
    en_route = "en_route"
    controle_depot = "controle_depot"
    valide = "valide"
    anomalie = "anomalie"


class ControleResultatEnum(str, enum.Enum):
    valide = "valide"
    anomalie = "anomalie"


class AlerteTypeEnum(str, enum.Enum):
    scelle_casse = "scelle_casse"
    ecart_quantite = "ecart_quantite"
    camion_non_attendu = "camion_non_attendu"
    signature_invalide = "signature_invalide"
    autre = "autre"


class AlerteGraviteEnum(str, enum.Enum):
    haute = "haute"
    moyenne = "moyenne"
    basse = "basse"


class AlerteStatutEnum(str, enum.Enum):
    ouverte = "ouverte"
    traitee = "traitee"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    matricule: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nom_complet: Mapped[str] = mapped_column(String(200))
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum))
    poste_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("postes.id"), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    poste: Mapped["Poste"] = relationship(back_populates="users")


class Poste(Base):
    __tablename__ = "postes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nom: Mapped[str] = mapped_column(String(120))
    type: Mapped[PosteTypeEnum] = mapped_column(Enum(PosteTypeEnum))
    ville: Mapped[str] = mapped_column(String(120))
    gps_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    cle_publique: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="poste")


class Transporteur(Base):
    __tablename__ = "transporteurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nom_societe: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    numero_agrement: Mapped[str | None] = mapped_column(String(60), nullable=True)


class Chauffeur(Base):
    __tablename__ = "chauffeurs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    nom_complet: Mapped[str] = mapped_column(String(200))
    numero_piece_identite: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)


class Vehicule(Base):
    __tablename__ = "vehicules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    plaque_immatriculation: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    type_citerne: Mapped[str | None] = mapped_column(String(120), nullable=True)
    capacite_max: Mapped[float | None] = mapped_column(Float, nullable=True)


class Manifeste(Base):
    __tablename__ = "manifestes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    vehicule_id: Mapped[str] = mapped_column(String(36), ForeignKey("vehicules.id"))
    transporteur_id: Mapped[str] = mapped_column(String(36), ForeignKey("transporteurs.id"))
    chauffeur_id: Mapped[str] = mapped_column(String(36), ForeignKey("chauffeurs.id"))
    poste_frontiere_id: Mapped[str] = mapped_column(String(36), ForeignKey("postes.id"))
    depot_destination_id: Mapped[str] = mapped_column(String(36), ForeignKey("postes.id"))
    type_cargaison: Mapped[CargaisonEnum] = mapped_column(Enum(CargaisonEnum))
    quantite_declaree: Mapped[float] = mapped_column(Float)
    unite: Mapped[UniteEnum] = mapped_column(Enum(UniteEnum))
    numero_scelle: Mapped[str] = mapped_column(String(60))
    photo_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    agent_frontiere_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    signature_numerique: Mapped[str] = mapped_column(Text)
    signature_valide: Mapped[bool] = mapped_column(Boolean, default=False)
    date_creation: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    statut: Mapped[ManifesteStatutEnum] = mapped_column(
        Enum(ManifesteStatutEnum), default=ManifesteStatutEnum.genere
    )
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ControleDepot(Base):
    __tablename__ = "controles_depot"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    manifeste_id: Mapped[str] = mapped_column(String(36), ForeignKey("manifestes.id"))
    agent_depot_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    scelle_intact: Mapped[bool] = mapped_column(Boolean)
    quantite_conforme: Mapped[bool] = mapped_column(Boolean)
    remarque: Mapped[str | None] = mapped_column(Text, nullable=True)
    resultat: Mapped[ControleResultatEnum] = mapped_column(Enum(ControleResultatEnum))
    date_controle: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Alerte(Base):
    __tablename__ = "alertes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    manifeste_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("manifestes.id"), nullable=True)
    type: Mapped[AlerteTypeEnum] = mapped_column(Enum(AlerteTypeEnum))
    gravite: Mapped[AlerteGraviteEnum] = mapped_column(Enum(AlerteGraviteEnum))
    description: Mapped[str] = mapped_column(Text)
    statut: Mapped[AlerteStatutEnum] = mapped_column(Enum(AlerteStatutEnum), default=AlerteStatutEnum.ouverte)
    date_creation: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    entite: Mapped[str] = mapped_column(String(60))
    entite_id: Mapped[str] = mapped_column(String(36))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
