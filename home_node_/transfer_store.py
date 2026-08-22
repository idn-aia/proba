from __future__ import annotations
from pathlib import Path
import time

class TransferStoreError(Exception): pass

AREAS=('incoming','from_pc','from_phone','outgoing','to_phone')
class TransferStore:
    def __init__(self, root: str | Path = 'simple_data', ttl_seconds=300):
        self.root=Path(root); self.ttl_seconds=ttl_seconds
        for area in AREAS: (self.root/area).mkdir(parents=True,exist_ok=True)
    def area_path(self,area):
        if area not in AREAS: raise TransferStoreError(f'Unknown area: {area}')
        return self.root/area
    def list_files(self,area): return [p for p in self.area_path(area).iterdir() if p.is_file()]
    def is_fresh(self,path): return time.time()-Path(path).stat().st_mtime <= self.ttl_seconds
    def cleanup_expired(self,area):
        removed=[]
        for p in self.list_files(area):
            if not self.is_fresh(p):
                try: p.unlink(); removed.append(p)
                except OSError: pass
        return removed
