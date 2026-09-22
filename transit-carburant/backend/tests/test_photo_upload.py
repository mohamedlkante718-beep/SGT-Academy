import base64
import io
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security import build_manifeste_payload


def _login(client, matricule, password):
    r = client.post("/auth/login", json={"matricule": matricule, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _creer_manifeste_synchronise(client, admin_token):
    r = client.post(
        "/postes",
        json={"nom": "Kourémalé", "type": "frontiere", "ville": "Kourémalé"},
        headers=_auth(admin_token),
    )
    poste_frontiere = r.json()
    cle_privee_b64 = poste_frontiere["cle_privee_a_provisionner"]
    poste_frontiere_id = poste_frontiere["poste"]["id"]

    r = client.post(
        "/postes",
        json={"nom": "Bamako", "type": "depot", "ville": "Bamako"},
        headers=_auth(admin_token),
    )
    depot_id = r.json()["poste"]["id"]

    r = client.post(
        "/users",
        json={
            "matricule": "DG-7777",
            "nom_complet": "Agent Photo",
            "role": "agent_frontiere",
            "poste_id": poste_frontiere_id,
            "password": "pass1234",
        },
        headers=_auth(admin_token),
    )
    agent_id = r.json()["id"]
    agent_token = _login(client, "DG-7777", "pass1234")

    manifeste_id = "55555555-5555-5555-5555-555555555555"
    date_creation = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    payload_bytes = build_manifeste_payload(
        manifeste_id=manifeste_id,
        plaque_immatriculation="ML-6001-PH",
        transporteur_nom="Photo Transport",
        chauffeur_nom="Test Chauffeur",
        type_cargaison="essence",
        quantite_declaree=20000.0,
        unite="litres",
        numero_scelle="SC-PHOTO",
        poste_frontiere_id=poste_frontiere_id,
        depot_destination_id=depot_id,
        date_creation_iso=date_creation,
    )
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(cle_privee_b64))
    signature_b64 = base64.b64encode(private_key.sign(payload_bytes)).decode("ascii")

    manifeste_payload = {
        "id": manifeste_id,
        "plaque_immatriculation": "ML-6001-PH",
        "transporteur_nom": "Photo Transport",
        "chauffeur_nom": "Test Chauffeur",
        "chauffeur_piece_identite": "CNI-7777",
        "poste_frontiere_id": poste_frontiere_id,
        "depot_destination_id": depot_id,
        "type_cargaison": "essence",
        "quantite_declaree": 20000.0,
        "unite": "litres",
        "numero_scelle": "SC-PHOTO",
        "agent_frontiere_id": agent_id,
        "signature_numerique": signature_b64,
        "date_creation": date_creation,
    }
    r = client.post(
        "/sync/manifestes",
        json={"manifestes": [manifeste_payload]},
        headers=_auth(agent_token),
    )
    assert r.status_code == 200, r.text

    return manifeste_id, agent_token


def test_upload_photo_puis_lecture_via_media(client):
    admin_token = _login(client, "admin", "admin1234")
    manifeste_id, agent_token = _creer_manifeste_synchronise(client, admin_token)

    fausse_image = io.BytesIO(b"\xff\xd8\xff\xe0contenu-jpeg-factice")
    r = client.post(
        f"/sync/manifestes/{manifeste_id}/photo",
        files={"fichier": ("citerne.jpg", fausse_image, "image/jpeg")},
        headers=_auth(agent_token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["manifeste_id"] == manifeste_id
    assert body["photo_path"] == f"/media/photos/{manifeste_id}.jpg"

    r = client.get(body["photo_path"])
    assert r.status_code == 200
    assert r.content == b"\xff\xd8\xff\xe0contenu-jpeg-factice"

    r = client.get("/dashboard/manifestes", headers=_auth(admin_token))
    manifeste = next(m for m in r.json() if m["id"] == manifeste_id)
    assert manifeste is not None


def test_upload_photo_format_non_supporte(client):
    admin_token = _login(client, "admin", "admin1234")
    manifeste_id, agent_token = _creer_manifeste_synchronise(client, admin_token)

    r = client.post(
        f"/sync/manifestes/{manifeste_id}/photo",
        files={"fichier": ("scelle.gif", io.BytesIO(b"GIF89a"), "image/gif")},
        headers=_auth(agent_token),
    )
    assert r.status_code == 400


def test_upload_photo_manifeste_introuvable(client):
    admin_token = _login(client, "admin", "admin1234")
    _, agent_token = _creer_manifeste_synchronise(client, admin_token)

    r = client.post(
        "/sync/manifestes/99999999-9999-9999-9999-999999999999/photo",
        files={"fichier": ("citerne.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")},
        headers=_auth(agent_token),
    )
    assert r.status_code == 404


def test_upload_photo_refuse_sans_authentification(client):
    admin_token = _login(client, "admin", "admin1234")
    manifeste_id, _ = _creer_manifeste_synchronise(client, admin_token)

    r = client.post(
        f"/sync/manifestes/{manifeste_id}/photo",
        files={"fichier": ("citerne.jpg", io.BytesIO(b"\xff\xd8\xff"), "image/jpeg")},
    )
    assert r.status_code == 401
