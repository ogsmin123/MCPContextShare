import time
from .base import Strategy

class PullOnDemand(Strategy):
    def __init__(self, agent_id, store, router, ttl_seconds=60):
        super().__init__(agent_id, store, router)
        self.ttl = ttl_seconds
        self.cache = {}  # cid -> (item, fetched_at)

    def read(self, cid: str):
        now = time.time()
        if cid in self.cache and now - self.cache[cid][1] < self.ttl:
            item = self.cache[cid][0]
            return item, (now - item.updated_at)*1000.0 if item else 0.0
        item = self.store.read(cid)
        self.cache[cid] = (item, now)
        return item, (now - item.updated_at)*1000.0 if item else 0.0

    def write(self, cid: str, data: str) -> bool:
        self.store.write(cid, data)
        return True
