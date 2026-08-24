from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass

DEFAULT_STORAGE_PATH = Path("home_node_data") / "node_data" / "paired_devices.json"
class PairedDevicesError(Exception): pass
@dataclass(frozen=True)
class PairedDevice:
    device_id: str
    name: str
    public_key: str | None = None
    def to_dict(self): return {"device_id":self.device_id,"name":self.name,"public_key":self.public_key}
    @classmethod
    def from_dict(cls, d): return cls(str(d["device_id"]), str(d.get("name", "")), d.get("public_key"))
class PairedDevicesStore:
    def __init__(self, storage_path=DEFAULT_STORAGE_PATH): self.storage_path=Path(storage_path); self._devices={}; self.load()
    def load(self):
        if not self.storage_path.exists(): self._devices={}; self.save(); return
        try: data=json.loads(self.storage_path.read_text(encoding="utf-8"))
        except Exception as exc: raise PairedDevicesError("Failed to load paired devices") from exc
        self._devices={d.device_id:d for d in (PairedDevice.from_dict(x) for x in data.get("devices",[]))}
    def save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True); self.storage_path.write_text(json.dumps({"version":1,"devices":[d.to_dict() for d in self._devices.values()]},indent=2),encoding="utf-8")
    def add(self, device): self._devices[device.device_id]=device; self.save()
    def get(self, device_id): return self._devices.get(device_id)
    def remove(self, device_id):
        if device_id not in self._devices:return False
        del self._devices[device_id]; self.save(); return True
    def all(self): return list(self._devices.values())
