from __future__ import annotations
import hashlib, secrets
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from identity import NodeIdentity, calculate_node_id

class NodeAuthError(Exception): pass
@dataclass(frozen=True)
class AuthChallenge:
    challenge: bytes
    sender_node_id: str
    receiver_node_id: str
@dataclass(frozen=True)
class AuthResponse:
    node_id: str
    public_key: bytes
    signature: bytes

def build_auth_payload(challenge: bytes, sender_node_id: str, receiver_node_id: str) -> bytes:
    return b"HOME_NODE_AUTH_V1\0" + challenge + b"\0" + sender_node_id.encode() + b"\0" + receiver_node_id.encode()

def create_auth_challenge(sender_node_id, receiver_node_id): return AuthChallenge(secrets.token_bytes(32), sender_node_id, receiver_node_id)
def create_auth_response(identity: NodeIdentity, challenge: AuthChallenge, receiver_node_id: str):
    payload=build_auth_payload(challenge.challenge, identity.node_id, receiver_node_id)
    return AuthResponse(identity.node_id, identity.public_key_bytes, identity.sign(payload))
def verify_node_id(node_id, public_key): return calculate_node_id(public_key)==node_id
def verify_auth_response(response, challenge, expected_node_id, receiver_node_id):
    if response.node_id != expected_node_id or not verify_node_id(response.node_id,response.public_key): return False
    try: Ed25519PublicKey.from_public_bytes(response.public_key).verify(response.signature, build_auth_payload(challenge.challenge,response.node_id,receiver_node_id)); return True
    except Exception: return False
