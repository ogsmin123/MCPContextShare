from dataclasses import dataclass
from typing import Dict, Optional
import time

@dataclass
class ContextItem:
    id: str
    version: int
    data: str
    updated_at: float

class ContextStore:
    def __init__(self):
        self.store: Dict[str, ContextItem] = {}

    def read(self, cid: str) -> Optional[ContextItem]:
        return self.store.get(cid)

    def write(self, cid: str, data: str) -> ContextItem:
        now = time.time()
        cur = self.store.get(cid)
        v = (cur.version + 1) if cur else 1
        item = ContextItem(id=cid, version=v, data=data, updated_at=now)
        self.store[cid] = item
        return item
