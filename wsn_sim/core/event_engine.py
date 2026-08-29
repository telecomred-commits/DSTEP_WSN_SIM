from dataclasses import dataclass, field
from heapq import heappush, heappop
from typing import Callable, Any

@dataclass(order=True)
class Event:
    time: float
    seq: int
    callback: Callable = field(compare=False)
    args: tuple = field(default_factory=tuple, compare=False)

class EventEngine:
    def __init__(self):
        self.time = 0.0
        self._queue = []
        self._seq = 0

    def schedule(self, time: float, callback: Callable, *args: Any):
        self._seq += 1
        heappush(self._queue, Event(time, self._seq, callback, args))

    def run(self, until: float):
        while self._queue:
            event = heappop(self._queue)
            if event.time > until:
                break
            self.time = event.time
            event.callback(*event.args)
        self.time = until
