import os
import tempfile

os.environ["JWT_SECRET"] = "test-secret"
os.environ["MEDIA_ROOT"] = tempfile.mkdtemp(prefix="transit_carburant_media_")
# Valeur nécessaire pour que le moteur global de app.database (créé une
# fois, à l'import) ait quelque chose de valide à pointer ; chaque test
# utilise en réalité sa PROPRE base isolée via override_get_db, jamais
# celle-ci.
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkstemp(suffix='_unused.db')[1]}")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import RoleEnum, User  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    """Un client de test avec sa PROPRE base SQLite isolée.

    Chaque test doit pouvoir créer ses postes/utilisateurs/manifestes
    sans jamais entrer en collision avec ceux d'un autre test (même
    matricule, même id, agrégats du tableau de bord...). Le bootstrap
    admin intégré à l'appli (voir app/main.py) cible le moteur global,
    pas cette base isolée : on le reproduit ici explicitement.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.add(
        User(
            matricule="admin",
            nom_complet="Administrateur initial",
            role=RoleEnum.admin,
            password_hash=hash_password("admin1234"),
        )
    )
    db.commit()
    db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
