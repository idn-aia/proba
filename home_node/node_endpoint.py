from __future__ import annotations
from dataclasses import dataclass
from protocol import encode_bytes, decode_bytes

class NodeEndpointError(Exception): pass

@dataclass(frozen=True)
class NodeEndpoint:
    node_id: str
    host: str
    port: int
    public_key: bytes | None = None
    def __post_init__(self):
        if not self.node_id or not isinstance(self.node_id, str): raise NodeEndpointError("invalid node_id")
        if not self.host or not isinstance(self.host, str): raise NodeEndpointError("invalid host")
        if not (1 <= self.port <= 65535): raise NodeEndpointError("invalid port")
        if self.public_key is not None and len(self.public_key) != 32: raise NodeEndpointError("public_key must be 32 bytes")
    def to_dict(self):
        d = {"node_id": self.node_id, "host": self.host, "port": self.port}
        if self.public_key is not None: d["public_key"] = encode_bytes(self.public_key)
        return d
    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict): raise NodeEndpointError("endpoint must be object")
        key = data.get("public_key")
        return cls(str(data["node_id"]), str(data["host"]), int(data["port"]), decode_bytes(key) if key else None)
