import base64
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from cryptography.exceptions import InvalidSignature
from jose import JWTError, jwt
from passlib.context import CryptContext

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def generate_poste_keypair() -> tuple[str, str]:
    """Génère une paire de clés Ed25519 pour un poste frontière.

    Retourne (cle_publique_b64, cle_privee_b64). La clé privée n'est
    JAMAIS stockée côté serveur : elle est renvoyée une seule fois à
    l'appel, à charge pour l'administrateur de la provisionner sur
    l'appareil de l'agent affecté à ce poste.
    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=Encoding.Raw, format=PrivateFormat.Raw, encryption_algorithm=NoEncryption()
    )
    public_bytes = public_key.public_bytes(encoding=Encoding.Raw, format=PublicFormat.Raw)

    return (
        base64.b64encode(public_bytes).decode("ascii"),
        base64.b64encode(private_bytes).decode("ascii"),
    )


def build_manifeste_payload(
    manifeste_id: str,
    plaque_immatriculation: str,
    transporteur_nom: str,
    chauffeur_nom: str,
    type_cargaison: str,
    quantite_declaree: float,
    unite: str,
    numero_scelle: str,
    poste_frontiere_id: str,
    depot_destination_id: str,
    date_creation_iso: str,
) -> bytes:
    """Construit le contenu canonique signé par le poste frontière.

    Cet ordre de champs et ce séparateur doivent être identiques côté
    mobile (Dart) et côté serveur (Python) : c'est ce texte, et rien
    d'autre, qui est signé puis vérifié.
    """
    parts = [
        manifeste_id,
        plaque_immatriculation,
        transporteur_nom,
        chauffeur_nom,
        type_cargaison,
        f"{quantite_declaree:.3f}",
        unite,
        numero_scelle,
        poste_frontiere_id,
        depot_destination_id,
        date_creation_iso,
    ]
    return "|".join(parts).encode("utf-8")


def verify_manifeste_signature(payload: bytes, signature_b64: str, public_key_b64: str) -> bool:
    try:
        public_key_bytes = base64.b64decode(public_key_b64)
        signature_bytes = base64.b64decode(signature_b64)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature_bytes, payload)
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False
