"""Wire protocol constants and canonical JSON helpers for Home Node v1."""
from __future__ import annotations
import base64, json

PROTOCOL_VERSION = 1
MAX_FRAME_SIZE = 8 * 1024 * 1024
CHUNK_SIZE = 256 * 1024

AUTH_CHALLENGE = "auth.challenge"
AUTH_RESPONSE = "auth.response"
AUTH_RESULT = "auth.result"
TRANSFER_OFFER = "transfer.offer"
TRANSFER_ACCEPT = "transfer.accept"
TRANSFER_CHUNK = "transfer.chunk"
TRANSFER_COMPLETE = "transfer.complete"
TRANSFER_ACK = "transfer.ack"
ERROR = "error"


def encode_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise TypeError("value must be bytes")
    return base64.b64encode(value).decode("ascii")


def decode_bytes(value: str) -> bytes:
    if not isinstance(value, str):
        raise TypeError("encoded value must be str")
    return base64.b64decode(value.encode("ascii"), validate=True)


def dumps_message(message: dict) -> bytes:
    if not isinstance(message, dict):
        raise TypeError("message must be dict")
    return json.dumps(message, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def loads_message(data: bytes) -> dict:
    obj = json.loads(data.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("message must be a JSON object")
    return obj
