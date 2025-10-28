import time
from dataclasses import dataclass
from typing import Optional
from .metrics import Metrics

@dataclass
class OpResult:
    op_id: int
    op: str  # read|write
    cid: str
    start: float
    end: float
    success: bool
    staleness_ms: float = 0.0
    conflict: bool = False
    version_seen: int = 0

class Agent:
    def __init__(self, agent_id: int, strategy, metrics: Metrics):
        self.id = agent_id
        self.strategy = strategy
        self.metrics = metrics
        self._op_id = 0

    def step(self, op: str, cid: str, payload: Optional[str]=None):
        self._op_id += 1
        start = time.time()
        if op == 'read':
            item, stale_ms = self.strategy.read(cid)
            ok = item is not None
            end = time.time()
            self.metrics.record_op(OpResult(self._op_id, op, cid, start, end, ok, stale_ms, False, item.version if item else 0))
        else:
            ok = self.strategy.write(cid, payload)
            end = time.time()
            self.metrics.record_op(OpResult(self._op_id, op, cid, start, end, ok, 0.0, False, 0))
