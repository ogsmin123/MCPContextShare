import time
from .base import Strategy
from .broadcast import Broadcast
from .pubsub import PubSub
from .pull_on_demand import PullOnDemand
from .hierarchical_cache import HierarchicalCache

class HybridAdaptive(Strategy):
    def __init__(self, agent_id, store, router, agent_count: int, read_ratio: float, access_skew: float=0.8):
        super().__init__(agent_id, store, router)
        self.cur = Broadcast(agent_id, store, router)
        self.agent_count = agent_count
        self.read_ratio = read_ratio
        self.access_skew = access_skew
        self.last_switch = time.time()

    def _select(self):
        if self.read_ratio <= 0.3:
            return PubSub(self.agent_id, self.store, self.router)
        if self.read_ratio > 0.7 and self.agent_count <= 25:
            return Broadcast(self.agent_id, self.store, self.router)
        if self.read_ratio > 0.7 and self.access_skew > 0.8:
            return HierarchicalCache(self.agent_id, self.store, self.router)
        if self.agent_count > 50:
            return PubSub(self.agent_id, self.store, self.router)
        return PullOnDemand(self.agent_id, self.store, self.router)

    def _maybe_switch(self):
        if time.time() - self.last_switch > 30:
            self.cur = self._select()
            self.last_switch = time.time()

    def read(self, cid: str):
        self._maybe_switch()
        return self.cur.read(cid)

    def write(self, cid: str, data: str) -> bool:
        self._maybe_switch()
        return self.cur.write(cid, data)
