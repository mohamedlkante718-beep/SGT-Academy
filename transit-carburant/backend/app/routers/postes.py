from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Poste, PosteTypeEnum
from app.schemas import PosteCreate, PosteCreated, PosteOut
from app.security import generate_poste_keypair

router = APIRouter(prefix="/postes", tags=["postes"])


@router.post("", response_model=PosteCreated, dependencies=[Depends(require_role("admin"))])
def create_poste(payload: PosteCreate, db: Session = Depends(get_db)) -> PosteCreated:
    poste = Poste(nom=payload.nom, type=payload.type, ville=payload.ville, gps_lat=payload.gps_lat, gps_lng=payload.gps_lng)

    cle_privee = ""
    if payload.type == PosteTypeEnum.frontiere:
        cle_publique, cle_privee = generate_poste_keypair()
        poste.cle_publique = cle_publique

    db.add(poste)
    db.commit()
    db.refresh(poste)

    return PosteCreated(poste=PosteOut.model_validate(poste), cle_privee_a_provisionner=cle_privee)


@router.get("", response_model=list[PosteOut])
def list_postes(db: Session = Depends(get_db)) -> list[Poste]:
    return db.query(Poste).all()


@router.get("/{poste_id}", response_model=PosteOut)
def get_poste(poste_id: str, db: Session = Depends(get_db)) -> Poste:
    poste = db.get(Poste, poste_id)
    if poste is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poste introuvable")
    return poste
