from .base import Strategy
from ..utils import sleep_ms

class Broadcast(Strategy):
    def read(self, cid: str):
        item = self.store.read(cid)
        stale_ms = 0.0 if item else 0.0
        return item, stale_ms

    def write(self, cid: str, data: str) -> bool:
        item = self.store.write(cid, data)
        self.router.broadcast(self.agent_id, {'type':'update','cid':cid,'version':item.version})
        sleep_ms(self.router.delay_ms)
        return True
