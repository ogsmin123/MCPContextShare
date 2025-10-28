from abc import ABC, abstractmethod
from typing import Optional
from ..context_store import ContextStore, ContextItem
from ..message_router import MessageRouter

class Strategy(ABC):
    def __init__(self, agent_id: int, store: ContextStore, router: MessageRouter):
        self.agent_id = agent_id
        self.store = store
        self.router = router
    @abstractmethod
    def read(self, cid: str) -> tuple[Optional[ContextItem], float]:
        ...
    @abstractmethod
    def write(self, cid: str, data: str) -> bool:
        ...
