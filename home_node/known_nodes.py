from __future__ import annotations
import json
from pathlib import Path
from node_endpoint import NodeEndpoint, NodeEndpointError

DEFAULT_STORAGE_PATH = Path("home_node_data") / "node_data" / "known_nodes.json"
class KnownNodesError(Exception): pass

class KnownNodesStore:
    def __init__(self, storage_path: str | Path = DEFAULT_STORAGE_PATH):
        self.storage_path = Path(storage_path); self._nodes = {}; self.load()
    def load(self):
        if not self.storage_path.exists(): self._nodes = {}; self.save(); return
        try: data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc: raise KnownNodesError("Failed to load known nodes") from exc
        loaded = {}
        for item in data.get("nodes", []):
            try: ep = NodeEndpoint.from_dict(item)
            except (NodeEndpointError, TypeError, KeyError, ValueError) as exc: raise KnownNodesError("Invalid node endpoint") from exc
            if ep.node_id in loaded: raise KnownNodesError(f"Duplicate NodeID: {ep.node_id}")
            loaded[ep.node_id] = ep
        self._nodes = loaded
    def save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.storage_path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version":1,"nodes":[n.to_dict() for n in self._nodes.values()]}, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.storage_path)
    def add(self, endpoint):
        if not isinstance(endpoint, NodeEndpoint): raise TypeError("endpoint must be NodeEndpoint")
        self._nodes[endpoint.node_id] = endpoint; self.save()
    def get(self, node_id): return self._nodes.get(node_id)
    def require(self, node_id):
        ep = self.get(node_id)
        if ep is None: raise KnownNodesError(f"Unknown NodeID: {node_id}")
        return ep
    def remove(self, node_id):
        if node_id not in self._nodes: return False
        del self._nodes[node_id]; self.save(); return True
    def contains(self, node_id): return node_id in self._nodes
    def all(self): return list(self._nodes.values())
    def __len__(self): return len(self._nodes)
