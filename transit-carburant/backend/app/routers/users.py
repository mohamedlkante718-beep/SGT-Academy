from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import User
from app.schemas import UserCreate, UserOut
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserOut, dependencies=[Depends(require_role("admin"))])
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.matricule == payload.matricule).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce matricule existe déjà")

    user = User(
        matricule=payload.matricule,
        nom_complet=payload.nom_complet,
        role=payload.role,
        poste_id=payload.poste_id,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserOut], dependencies=[Depends(require_role("admin", "superviseur"))])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).all()
