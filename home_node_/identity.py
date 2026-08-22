"""Persistent Ed25519 identity for a Home Node."""
from __future__ import annotations
from pathlib import Path
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

DEFAULT_DATA_DIR = Path("home_node_data") / "home_node_key"
PRIVATE_KEY_FILENAME = "node_private.key"
PUBLIC_KEY_FILENAME = "node_public.key"

class IdentityError(Exception): pass

def calculate_node_id(public_key_bytes: bytes) -> str:
    if not isinstance(public_key_bytes, bytes) or not public_key_bytes: raise ValueError("public_key_bytes must be non-empty bytes")
    return hashlib.sha256(public_key_bytes).digest()[:16].hex()

class NodeIdentity:
    def __init__(self, data_dir: str | Path | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
        self.private_key_path = self.data_dir / PRIVATE_KEY_FILENAME
        self.public_key_path = self.data_dir / PUBLIC_KEY_FILENAME
        self._private_key: Ed25519PrivateKey
        self._public_key: Ed25519PublicKey
        self._load_or_create()

    def _load_or_create(self):
        p, q = self.private_key_path.exists(), self.public_key_path.exists()
        if p and q: self._load_existing()
        elif p or q: raise IdentityError("Incomplete identity: both key files are required")
        else: self._create_new()

    def _create_new(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._private_key = Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self.private_key_path.write_bytes(self._private_key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
        self.public_key_path.write_bytes(self._public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw))

    def _load_existing(self):
        private_bytes, public_bytes = self.private_key_path.read_bytes(), self.public_key_path.read_bytes()
        if len(private_bytes) != 32 or len(public_bytes) != 32: raise IdentityError("Invalid Ed25519 key length")
        try:
            self._private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
            self._public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
            derived = self._private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        except Exception as exc: raise IdentityError("Invalid identity key data") from exc
        if derived != public_bytes: raise IdentityError("Private and public keys do not match")

    @property
    def public_key_bytes(self) -> bytes:
        return self._public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    @property
    def node_id(self) -> str:
        return calculate_node_id(self.public_key_bytes)

    def sign(self, data: bytes) -> bytes: return self._private_key.sign(data)
    def verify(self, data: bytes, signature: bytes) -> bool:
        try: self._public_key.verify(signature, data); return True
        except Exception: return False
    def public_key_hex(self) -> str: return self.public_key_bytes.hex()
