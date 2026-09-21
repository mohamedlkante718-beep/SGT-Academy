import base64
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.security import build_manifeste_payload


def _login(client, matricule, password):
    r = client.post("/auth/login", json={"matricule": matricule, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_parcours_complet_frontiere_vers_depot(client):
    admin_token = _login(client, "admin", "admin1234")

    r = client.post(
        "/postes",
        json={"nom": "Kourémalé", "type": "frontiere", "ville": "Kourémalé"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    poste_frontiere = r.json()
    cle_privee_b64 = poste_frontiere["cle_privee_a_provisionner"]
    poste_frontiere_id = poste_frontiere["poste"]["id"]
    assert poste_frontiere["poste"]["cle_publique"]

    r = client.post(
        "/postes",
        json={"nom": "Bamako", "type": "depot", "ville": "Bamako"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    depot_id = r.json()["poste"]["id"]

    r = client.post(
        "/users",
        json={
            "matricule": "DG-0245",
            "nom_complet": "Agent Frontière",
            "role": "agent_frontiere",
            "poste_id": poste_frontiere_id,
            "password": "pass1234",
        },
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    agent_frontiere_id = r.json()["id"]

    r = client.post(
        "/users",
        json={
            "matricule": "DP-0110",
            "nom_complet": "Agent Dépôt",
            "role": "agent_depot",
            "poste_id": depot_id,
            "password": "pass1234",
        },
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    agent_depot_id = r.json()["id"]

    agent_frontiere_token = _login(client, "DG-0245", "pass1234")
    agent_depot_token = _login(client, "DP-0110", "pass1234")

    manifeste_id = "11111111-1111-1111-1111-111111111111"
    date_creation = datetime.now(timezone.utc).replace(microsecond=0)

    payload_bytes = build_manifeste_payload(
        manifeste_id=manifeste_id,
        plaque_immatriculation="ML-4521-AB",
        transporteur_nom="STMB Transport",
        chauffeur_nom="Amadou Traoré",
        type_cargaison="essence",
        quantite_declaree=32000.0,
        unite="litres",
        numero_scelle="SC-88213",
        poste_frontiere_id=poste_frontiere_id,
        depot_destination_id=depot_id,
        date_creation_iso=date_creation.isoformat(),
    )
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(cle_privee_b64))
    signature_b64 = base64.b64encode(private_key.sign(payload_bytes)).decode("ascii")

    manifeste_payload = {
        "id": manifeste_id,
        "plaque_immatriculation": "ML-4521-AB",
        "transporteur_nom": "STMB Transport",
        "chauffeur_nom": "Amadou Traoré",
        "chauffeur_piece_identite": "CNI-99887",
        "poste_frontiere_id": poste_frontiere_id,
        "depot_destination_id": depot_id,
        "type_cargaison": "essence",
        "quantite_declaree": 32000.0,
        "unite": "litres",
        "numero_scelle": "SC-88213",
        "agent_frontiere_id": agent_frontiere_id,
        "signature_numerique": signature_b64,
        "date_creation": date_creation.isoformat(),
    }

    r = client.post(
        "/sync/manifestes",
        json={"manifestes": [manifeste_payload]},
        headers=_auth(agent_frontiere_token),
    )
    assert r.status_code == 200, r.text
    resultat = r.json()["resultats"][0]
    assert resultat["signature_valide"] is True
    assert resultat["statut"] == "en_route"

    # Renvoyer le même manifeste (retry réseau typique en hors-ligne) : idempotent.
    r = client.post(
        "/sync/manifestes",
        json={"manifestes": [manifeste_payload]},
        headers=_auth(agent_frontiere_token),
    )
    assert r.status_code == 200
    assert len(r.json()["resultats"]) == 1

    controle_payload = {
        "id": "22222222-2222-2222-2222-222222222222",
        "manifeste_id": manifeste_id,
        "agent_depot_id": agent_depot_id,
        "scelle_intact": True,
        "quantite_conforme": True,
        "resultat": "valide",
        "date_controle": datetime.now(timezone.utc).isoformat(),
    }
    r = client.post(
        "/sync/controles",
        json={"controles": [controle_payload]},
        headers=_auth(agent_depot_token),
    )
    assert r.status_code == 200, r.text
    assert r.json()["resultats"][0]["resultat"] == "valide"

    r = client.post(
        "/users",
        json={"matricule": "SUP-01", "nom_complet": "Superviseur", "role": "superviseur", "password": "pass1234"},
        headers=_auth(admin_token),
    )
    assert r.status_code == 200, r.text
    superviseur_token = _login(client, "SUP-01", "pass1234")

    r = client.get("/dashboard/summary", headers=_auth(superviseur_token))
    assert r.status_code == 200, r.text
    summary = r.json()
    assert summary["camions_au_depot_aujourdhui"] == 1
    assert summary["volume_total_aujourdhui"] == 32000.0

    r = client.get("/dashboard/manifestes", headers=_auth(superviseur_token))
    assert r.status_code == 200
    assert any(m["id"] == manifeste_id for m in r.json())


def test_signature_invalide_declenche_une_alerte(client):
    admin_token = _login(client, "admin", "admin1234")

    r = client.post(
        "/postes",
        json={"nom": "Zégoua", "type": "frontiere", "ville": "Zégoua"},
        headers=_auth(admin_token),
    )
    poste_id = r.json()["poste"]["id"]

    r = client.post(
        "/postes",
        json={"nom": "Ségou", "type": "depot", "ville": "Ségou"},
        headers=_auth(admin_token),
    )
    depot_id = r.json()["poste"]["id"]

    r = client.post(
        "/users",
        json={
            "matricule": "DG-9999",
            "nom_complet": "Agent Test",
            "role": "agent_frontiere",
            "poste_id": poste_id,
            "password": "pass1234",
        },
        headers=_auth(admin_token),
    )
    agent_id = r.json()["id"]
    agent_token = _login(client, "DG-9999", "pass1234")

    manifeste_payload = {
        "id": "33333333-3333-3333-3333-333333333333",
        "plaque_immatriculation": "ML-0000-ZZ",
        "transporteur_nom": "Inconnu",
        "chauffeur_nom": "Inconnu",
        "chauffeur_piece_identite": "CNI-000",
        "poste_frontiere_id": poste_id,
        "depot_destination_id": depot_id,
        "type_cargaison": "gasoil",
        "quantite_declaree": 1000.0,
        "unite": "litres",
        "numero_scelle": "SC-000",
        "agent_frontiere_id": agent_id,
        "signature_numerique": base64.b64encode(b"signature-invalide-ou-corrompue").decode("ascii"),
        "date_creation": datetime.now(timezone.utc).isoformat(),
    }

    r = client.post(
        "/sync/manifestes",
        json={"manifestes": [manifeste_payload]},
        headers=_auth(agent_token),
    )
    assert r.status_code == 200, r.text
    resultat = r.json()["resultats"][0]
    assert resultat["signature_valide"] is False
    assert resultat["statut"] == "anomalie"


def test_login_refuse_mauvais_mot_de_passe(client):
    r = client.post("/auth/login", json={"matricule": "admin", "password": "mauvais"})
    assert r.status_code == 401
