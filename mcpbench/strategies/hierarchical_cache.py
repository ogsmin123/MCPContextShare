import time
from .base import Strategy

class HierarchicalCache(Strategy):
    L2_groups = {}

    def __init__(self, agent_id, store, router, group_mod=5, l1_capacity=100, l2_capacity=1000):
        super().__init__(agent_id, store, router)
        self.group = agent_id % group_mod
        if self.group not in HierarchicalCache.L2_groups:
            HierarchicalCache.L2_groups[self.group] = {}
        self.L1 = {}
        self.l1_capacity = l1_capacity
        self.l2_capacity = l2_capacity

    def _l2(self):
        return HierarchicalCache.L2_groups[self.group]

    def _promote(self, cid, item):
        self.L1[cid] = (item, time.time())
        if len(self.L1) > self.l1_capacity:
            self.L1.pop(next(iter(self.L1)))
        l2 = self._l2()
        l2[cid] = (item, time.time())
        if len(l2) > self.l2_capacity:
            l2.pop(next(iter(l2)))

    def read(self, cid: str):
        now = time.time()
        if cid in self.L1:
            item = self.L1[cid][0]
            return item, (now - item.updated_at)*1000.0 if item else 0.0
        l2 = self._l2()
        if cid in l2:
            item = l2[cid][0]
            self._promote(cid, item)
            return item, (now - item.updated_at)*1000.0 if item else 0.0
        item = self.store.read(cid)
        if item:
            self._promote(cid, item)
        return item, (now - item.updated_at)*1000.0 if item else 0.0

    def write(self, cid: str, data: str) -> bool:
        item = self.store.write(cid, data)
        self.L1.pop(cid, None)
        self._l2().pop(cid, None)
        return True
