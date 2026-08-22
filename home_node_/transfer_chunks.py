from __future__ import annotations
import hashlib
from pathlib import Path
from protocol import CHUNK_SIZE

class TransferChunkError(Exception): pass

def iter_file_chunks(path: str | Path, chunk_size=CHUNK_SIZE):
    with Path(path).open('rb') as f:
        index=0
        while data:=f.read(chunk_size):
            yield index,data
            index+=1

def write_chunk(path: str | Path, data: bytes, expected_hash: str | None=None):
    if expected_hash and hashlib.sha256(data).hexdigest()!=expected_hash: raise TransferChunkError('Chunk hash mismatch')
    Path(path).write_bytes(data)
