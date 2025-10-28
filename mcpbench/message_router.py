from collections import defaultdict, deque
from typing import Dict, Deque, Set
from .utils import sleep_ms

class MessageRouter:
    def __init__(self, delay_ms: int = 5):
        self.delay_ms = delay_ms
        self.subscribers: Dict[str, Set[int]] = defaultdict(set)  # topic -> agent ids
        self.queues: Dict[int, Deque] = defaultdict(deque)

    def subscribe(self, agent_id: int, topic: str):
        self.subscribers[topic].add(agent_id)

    def unsubscribe(self, agent_id: int, topic: str):
        self.subscribers[topic].discard(agent_id)

    def broadcast(self, from_id: int, payload: dict):
        sleep_ms(self.delay_ms)
        for aid in list(self.queues.keys()):
            if aid != from_id:
                self.queues[aid].append(payload)

    def publish(self, topic: str, payload: dict):
        sleep_ms(self.delay_ms)
        for aid in self.subscribers.get(topic, set()):
            self.queues[aid].append(payload)

    def poll(self, agent_id: int):
        q = self.queues[agent_id]
        if q:
            return q.popleft()
        return None
