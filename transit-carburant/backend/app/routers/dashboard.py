from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Alerte, AlerteStatutEnum, Manifeste, ManifesteStatutEnum
from app.schemas import AlerteOut, DashboardSummary, ManifesteOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_SUPERVISEUR_ROLES = ("superviseur", "admin")


@router.get("/manifestes", response_model=list[ManifesteOut], dependencies=[Depends(require_role(*_SUPERVISEUR_ROLES))])
def list_manifestes(db: Session = Depends(get_db)) -> list[Manifeste]:
    return db.query(Manifeste).order_by(Manifeste.date_creation.desc()).limit(200).all()


@router.get("/alertes", response_model=list[AlerteOut], dependencies=[Depends(require_role(*_SUPERVISEUR_ROLES))])
def list_alertes(db: Session = Depends(get_db)) -> list[Alerte]:
    return (
        db.query(Alerte)
        .filter(Alerte.statut == AlerteStatutEnum.ouverte)
        .order_by(Alerte.date_creation.desc())
        .limit(100)
        .all()
    )


@router.get("/summary", response_model=DashboardSummary, dependencies=[Depends(require_role(*_SUPERVISEUR_ROLES))])
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)

    camions_en_transit = (
        db.query(Manifeste).filter(Manifeste.statut == ManifesteStatutEnum.en_route).count()
    )
    camions_au_depot_aujourdhui = (
        db.query(Manifeste)
        .filter(Manifeste.statut == ManifesteStatutEnum.valide, Manifeste.received_at >= today_start)
        .count()
    )
    alertes_actives = db.query(Alerte).filter(Alerte.statut == AlerteStatutEnum.ouverte).count()
    volume_total_aujourdhui = (
        db.query(func.coalesce(func.sum(Manifeste.quantite_declaree), 0.0))
        .filter(Manifeste.received_at >= today_start)
        .scalar()
    )

    return DashboardSummary(
        camions_en_transit=camions_en_transit,
        camions_au_depot_aujourdhui=camions_au_depot_aujourdhui,
        alertes_actives=alertes_actives,
        volume_total_aujourdhui=float(volume_total_aujourdhui or 0.0),
    )
