"""Vérifie que le backend fonctionne réellement sur PostgreSQL, pas
seulement sur la base SQLite utilisée par le reste de la suite.

Ignoré par défaut ; à activer avec :

    TEST_DATABASE_URL=postgresql://user:password@localhost/dbname pytest tests/test_postgres_compat.py

(par exemple avec un PostgreSQL local, ou le service `db` de
`docker-compose.yml`). Volontairement absent de la CI par défaut tant
qu'aucun PostgreSQL n'y est provisionné — voir `docs/DEPLOIEMENT.md`
pour le contexte : c'est ce test qui a servi à valider le passage de
SQLite (développement) à PostgreSQL (production).

IMPORTANT pour qui modifie ce fichier : ne JAMAIS s'appuyer sur
`app.database.engine` ou sur la variable d'environnement
`DATABASE_URL` ici. `conftest.py` a déjà importé `app.main` (donc
`app.database`) au chargement de la session pytest, avec sa propre
base SQLite jetable — modifier `DATABASE_URL` après coup ne rouvre pas
ce module déjà mis en cache par Python. Il faut créer un moteur
PostgreSQL explicite et l'injecter via `app.dependency_overrides`,
exactement comme le fait la fixture `client` de `conftest.py` (leçon
apprise : une première version de ce fichier semblait passer alors
qu'elle validait silencieusement la mauvaise base SQLite).
"""

import base64
import io
import os
import tempfile
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL non défini : voir la docstring de ce fichier",
)


@pytest.fixture()
def postgres_client():
    from fastapi.testclient import TestClient

    from app.database import Base, get_db
    from app.main import app
    from app.models import RoleEnum, User
    from app.security import hash_password

    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Repart d'une base propre : les types ENUM de PostgreSQL ne
    # supportent pas un CREATE TYPE répété comme le ferait SQLite.
    Base.metadata.drop_all(bind=engine)
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
    os.environ["MEDIA_ROOT"] = tempfile.mkdtemp(prefix="pg_compat_media_")

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_parcours_complet_sur_postgresql(postgres_client):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from app.security import build_manifeste_payload

    client = postgres_client

    r = client.get("/health")
    assert r.status_code == 200

    r = client.post("/auth/login", json={"matricule": "admin", "password": "admin1234"})
    assert r.status_code == 200, r.text
    admin_token = r.json()["access_token"]

    r = client.post(
        "/postes", json={"nom": "Kourémalé", "type": "frontiere", "ville": "Kourémalé"}, headers=_auth(admin_token)
    )
    assert r.status_code == 200, r.text
    poste_frontiere = r.json()
    cle_privee_b64 = poste_frontiere["cle_privee_a_provisionner"]
    poste_frontiere_id = poste_frontiere["poste"]["id"]
    assert poste_frontiere["poste"]["cle_publique"]

    r = client.post("/postes", json={"nom": "Bamako", "type": "depot", "ville": "Bamako"}, headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    depot_id = r.json()["poste"]["id"]

    r = client.post(
        "/users",
        json={
            "matricule": "DG-PG",
            "nom_complet": "Agent Postgres",
            "role": "agent_frontiere",
            "poste_id": poste_frontiere_id,
            "password": "pass1234",
        },
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    agent_id = r.json()["id"]

    r = client.post("/auth/login", json={"matricule": "DG-PG", "password": "pass1234"})
    assert r.status_code == 200, r.text
    agent_token = r.json()["access_token"]

    manifeste_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    date_creation_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    payload_bytes = build_manifeste_payload(
        manifeste_id=manifeste_id,
        plaque_immatriculation="ML-0001-PG",
        transporteur_nom="Postgres Test",
        chauffeur_nom="Chauffeur Test",
        type_cargaison="essence",
        quantite_declaree=15000.0,
        unite="litres",
        numero_scelle="SC-PG",
        poste_frontiere_id=poste_frontiere_id,
        depot_destination_id=depot_id,
        date_creation_iso=date_creation_iso,
    )
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(cle_privee_b64))
    signature_b64 = base64.b64encode(private_key.sign(payload_bytes)).decode("ascii")

    manifeste_payload = {
        "id": manifeste_id,
        "plaque_immatriculation": "ML-0001-PG",
        "transporteur_nom": "Postgres Test",
        "chauffeur_nom": "Chauffeur Test",
        "chauffeur_piece_identite": "CNI-PG",
        "poste_frontiere_id": poste_frontiere_id,
        "depot_destination_id": depot_id,
        "type_cargaison": "essence",
        "quantite_declaree": 15000.0,
        "unite": "litres",
        "numero_scelle": "SC-PG",
        "agent_frontiere_id": agent_id,
        "signature_numerique": signature_b64,
        "date_creation": date_creation_iso,
    }
    r = client.post("/sync/manifestes", json={"manifestes": [manifeste_payload]}, headers=_auth(agent_token))
    assert r.status_code == 200, r.text
    resultat = r.json()["resultats"][0]
    assert resultat["signature_valide"] is True

    r = client.post(
        f"/sync/manifestes/{manifeste_id}/photo",
        files={"fichier": ("citerne.jpg", io.BytesIO(b"\xff\xd8\xff\xe0-fake-jpeg"), "image/jpeg")},
        headers=_auth(agent_token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["photo_path"] == f"/media/photos/{manifeste_id}.jpg"

    r = client.get("/dashboard/summary", headers=_auth(admin_token))
    assert r.status_code == 200, r.text
    assert r.json()["volume_total_aujourdhui"] == 15000.0
