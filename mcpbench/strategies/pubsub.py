from .base import Strategy

class PubSub(Strategy):
    def __init__(self, agent_id, store, router):
        super().__init__(agent_id, store, router)
        self.topic_cache = {}

    def _topic(self, cid:str)->str:
        return f"t{hash(cid)%256}"

    def read(self, cid: str):
        item = self.store.read(cid)
        m = self.router.poll(self.agent_id)
        while m:
            m = self.router.poll(self.agent_id)
        stale = 2.0 if item else 0.0
        return item, stale

    def write(self, cid: str, data: str) -> bool:
        item = self.store.write(cid, data)
        self.router.publish(self._topic(cid), {'type':'update','cid':cid,'version':item.version})
        return True
