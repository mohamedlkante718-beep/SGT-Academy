import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import PHOTOS_DIR
from app.database import get_db
from app.deps import require_role
from app.models import (
    Alerte,
    AlerteGraviteEnum,
    AlerteStatutEnum,
    AlerteTypeEnum,
    Chauffeur,
    ControleDepot,
    ControleResultatEnum,
    Manifeste,
    ManifesteStatutEnum,
    Poste,
    Transporteur,
    Vehicule,
)
from app.schemas import (
    ControleBatchIn,
    ControleBatchOut,
    ControleOut,
    ManifesteBatchIn,
    ManifesteBatchOut,
    ManifestePhotoOut,
    ManifesteSyncResult,
)
from app.security import build_manifeste_payload, verify_manifeste_signature

router = APIRouter(prefix="/sync", tags=["sync"])

_EXTENSIONS_AUTORISEES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _get_or_create_vehicule(db: Session, plaque: str, type_citerne: str | None) -> Vehicule:
    vehicule = db.query(Vehicule).filter(Vehicule.plaque_immatriculation == plaque).first()
    if vehicule is None:
        vehicule = Vehicule(plaque_immatriculation=plaque, type_citerne=type_citerne)
        db.add(vehicule)
        db.flush()
    return vehicule


def _get_or_create_transporteur(db: Session, nom: str, telephone: str | None) -> Transporteur:
    transporteur = db.query(Transporteur).filter(Transporteur.nom_societe == nom).first()
    if transporteur is None:
        transporteur = Transporteur(nom_societe=nom, telephone=telephone)
        db.add(transporteur)
        db.flush()
    return transporteur


def _get_or_create_chauffeur(db: Session, nom: str, piece_identite: str, telephone: str | None) -> Chauffeur:
    chauffeur = db.query(Chauffeur).filter(Chauffeur.numero_piece_identite == piece_identite).first()
    if chauffeur is None:
        chauffeur = Chauffeur(nom_complet=nom, numero_piece_identite=piece_identite, telephone=telephone)
        db.add(chauffeur)
        db.flush()
    return chauffeur


def _parse_iso_datetime(value: str) -> datetime:
    """Convertit la chaîne ISO-8601 brute du client en datetime, pour
    le STOCKAGE uniquement (jamais pour reconstruire le texte signé :
    voir la note sur `ManifesteIn.date_creation`)."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@router.post(
    "/manifestes",
    response_model=ManifesteBatchOut,
    dependencies=[Depends(require_role("agent_frontiere", "admin"))],
)
def sync_manifestes(payload: ManifesteBatchIn, db: Session = Depends(get_db)) -> ManifesteBatchOut:
    """Reçoit un lot de manifestes créés hors ligne.

    Idempotent : l'id est généré côté téléphone (UUID) et sert de clé
    primaire ; renvoyer deux fois le même manifeste ne crée jamais de
    doublon, il est simplement ignoré la deuxième fois.
    """
    resultats: list[ManifesteSyncResult] = []

    for item in payload.manifestes:
        existing = db.get(Manifeste, item.id)
        if existing is not None:
            resultats.append(
                ManifesteSyncResult(id=existing.id, signature_valide=existing.signature_valide, statut=existing.statut)
            )
            continue

        vehicule = _get_or_create_vehicule(db, item.plaque_immatriculation, item.type_citerne)
        transporteur = _get_or_create_transporteur(db, item.transporteur_nom, item.transporteur_telephone)
        chauffeur = _get_or_create_chauffeur(
            db, item.chauffeur_nom, item.chauffeur_piece_identite, item.chauffeur_telephone
        )

        poste_frontiere = db.get(Poste, item.poste_frontiere_id)

        signature_valide = False
        if poste_frontiere is not None and poste_frontiere.cle_publique:
            payload_bytes = build_manifeste_payload(
                manifeste_id=item.id,
                plaque_immatriculation=item.plaque_immatriculation,
                transporteur_nom=item.transporteur_nom,
                chauffeur_nom=item.chauffeur_nom,
                type_cargaison=item.type_cargaison.value,
                quantite_declaree=item.quantite_declaree,
                unite=item.unite.value,
                numero_scelle=item.numero_scelle,
                poste_frontiere_id=item.poste_frontiere_id,
                depot_destination_id=item.depot_destination_id,
                date_creation_iso=item.date_creation,
            )
            signature_valide = verify_manifeste_signature(
                payload_bytes, item.signature_numerique, poste_frontiere.cle_publique
            )

        manifeste = Manifeste(
            id=item.id,
            vehicule_id=vehicule.id,
            transporteur_id=transporteur.id,
            chauffeur_id=chauffeur.id,
            poste_frontiere_id=item.poste_frontiere_id,
            depot_destination_id=item.depot_destination_id,
            type_cargaison=item.type_cargaison,
            quantite_declaree=item.quantite_declaree,
            unite=item.unite,
            numero_scelle=item.numero_scelle,
            photo_path=item.photo_path,
            agent_frontiere_id=item.agent_frontiere_id,
            signature_numerique=item.signature_numerique,
            signature_valide=signature_valide,
            date_creation=_parse_iso_datetime(item.date_creation),
            statut=ManifesteStatutEnum.en_route if signature_valide else ManifesteStatutEnum.anomalie,
        )
        db.add(manifeste)
        db.flush()

        if not signature_valide:
            db.add(
                Alerte(
                    manifeste_id=manifeste.id,
                    type=AlerteTypeEnum.signature_invalide,
                    gravite=AlerteGraviteEnum.haute,
                    description=f"Signature invalide ou poste inconnu pour le manifeste {manifeste.id}",
                )
            )

        resultats.append(
            ManifesteSyncResult(id=manifeste.id, signature_valide=signature_valide, statut=manifeste.statut)
        )

    db.commit()
    return ManifesteBatchOut(resultats=resultats)


@router.post(
    "/controles",
    response_model=ControleBatchOut,
    dependencies=[Depends(require_role("agent_depot", "admin"))],
)
def sync_controles(payload: ControleBatchIn, db: Session = Depends(get_db)) -> ControleBatchOut:
    resultats: list[ControleOut] = []

    for item in payload.controles:
        existing = db.get(ControleDepot, item.id)
        if existing is not None:
            resultats.append(ControleOut(id=existing.id, manifeste_id=existing.manifeste_id, resultat=existing.resultat))
            continue

        controle = ControleDepot(
            id=item.id,
            manifeste_id=item.manifeste_id,
            agent_depot_id=item.agent_depot_id,
            scelle_intact=item.scelle_intact,
            quantite_conforme=item.quantite_conforme,
            remarque=item.remarque,
            resultat=item.resultat,
            date_controle=item.date_controle,
        )
        db.add(controle)

        manifeste = db.get(Manifeste, item.manifeste_id)
        if manifeste is not None:
            manifeste.statut = (
                ManifesteStatutEnum.valide if item.resultat == ControleResultatEnum.valide else ManifesteStatutEnum.anomalie
            )

            if not item.scelle_intact:
                db.add(
                    Alerte(
                        manifeste_id=manifeste.id,
                        type=AlerteTypeEnum.scelle_casse,
                        gravite=AlerteGraviteEnum.haute,
                        description=f"Scellé cassé signalé au dépôt pour le manifeste {manifeste.id}",
                    )
                )
            if not item.quantite_conforme:
                db.add(
                    Alerte(
                        manifeste_id=manifeste.id,
                        type=AlerteTypeEnum.ecart_quantite,
                        gravite=AlerteGraviteEnum.moyenne,
                        description=f"Écart de quantité signalé au dépôt pour le manifeste {manifeste.id}",
                    )
                )

        db.flush()
        resultats.append(ControleOut(id=controle.id, manifeste_id=controle.manifeste_id, resultat=controle.resultat))

    db.commit()
    return ControleBatchOut(resultats=resultats)


_TAILLE_PHOTO_MAX_OCTETS = 8 * 1024 * 1024


@router.post(
    "/manifestes/{manifeste_id}/photo",
    response_model=ManifestePhotoOut,
    dependencies=[Depends(require_role("agent_frontiere", "admin"))],
)
async def uploader_photo_manifeste(
    manifeste_id: str, fichier: UploadFile, db: Session = Depends(get_db)
) -> ManifestePhotoOut:
    """Reçoit la photo de la citerne/du scellé, prise hors ligne à la
    frontière et envoyée séparément une fois la synchronisation des
    données (plus légère et prioritaire) déjà passée.
    """
    manifeste = db.get(Manifeste, manifeste_id)
    if manifeste is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manifeste introuvable")

    extension = _EXTENSIONS_AUTORISEES.get(fichier.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format d'image non supporté (jpeg, png ou webp uniquement)",
        )

    contenu = await fichier.read()
    if len(contenu) > _TAILLE_PHOTO_MAX_OCTETS:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Photo trop volumineuse (max 8 Mo)")

    try:
        # Normalise et valide au passage : le nom de fichier ne doit
        # jamais dépendre directement d'une valeur fournie par le
        # client (risque de traversée de chemin).
        nom_fichier = f"{uuid.UUID(manifeste_id)}{extension}"
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identifiant de manifeste invalide")

    (PHOTOS_DIR / nom_fichier).write_bytes(contenu)

    manifeste.photo_path = f"/media/photos/{nom_fichier}"
    db.commit()

    return ManifestePhotoOut(manifeste_id=manifeste.id, photo_path=manifeste.photo_path)
