import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import MEDIA_ROOT, PHOTOS_DIR
from app.database import Base, SessionLocal, engine
from app.models import RoleEnum, User
from app.routers import auth, dashboard, postes, sync, users
from app.security import hash_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _bootstrap_admin()
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="TransitCarburant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(postes.router)
app.include_router(sync.router)
app.include_router(dashboard.router)

MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_ROOT)), name="media")


def _bootstrap_admin() -> None:
    """Crée un compte administrateur initial si la base est vide.

    Nécessaire pour amorcer le système : le premier admin sert ensuite
    à créer les postes et les comptes des agents via l'API.
    """
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            return
        matricule = os.getenv("ADMIN_BOOTSTRAP_MATRICULE", "admin")
        password = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "admin1234")
        db.add(
            User(
                matricule=matricule,
                nom_complet="Administrateur initial",
                role=RoleEnum.admin,
                password_hash=hash_password(password),
            )
        )
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
