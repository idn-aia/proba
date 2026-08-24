from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib, uuid

class TransferError(Exception): pass

@dataclass(frozen=True)
class TransferMeta:
    transfer_id: str
    sender_node_id: str
    recipient_node_id: str
    filename: str
    size: int
    sha256: str
    def to_dict(self): return self.__dict__.copy()
    @classmethod
    def from_dict(cls,d): return cls(d['transfer_id'],d['sender_node_id'],d['recipient_node_id'],d['filename'],int(d['size']),d['sha256'])

def new_transfer_id(): return uuid.uuid4().hex

def sha256_file(path: str | Path, chunk_size=1024*1024):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk:=f.read(chunk_size): h.update(chunk)
    return h.hexdigest()

def make_transfer_meta(path, sender_node_id, recipient_node_id):
    p=Path(path)
    if not p.is_file(): raise TransferError(f'File not found: {p}')
    return TransferMeta(new_transfer_id(),sender_node_id,recipient_node_id,p.name,p.stat().st_size,sha256_file(p))
