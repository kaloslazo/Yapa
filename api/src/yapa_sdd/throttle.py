"""Límites por dirección (iteración 51). Spec: docs/desarrollo/51-cierre-de-huecos-para-main.md (S-264, S-265)."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta


class Throttle:
    """Cuenta eventos por clave en una ventana móvil; guarda a lo más `max_keys` claves (las más viejas se olvidan)."""

    def __init__(self, limit: int, window: timedelta, max_keys: int = 10_000):
        self.limit, self.window, self.max_keys = limit, window, max_keys
        self.events: dict[str, deque] = {}

    def _recent(self, key: str, now: datetime) -> deque:
        events = self.events.get(key, deque())
        while events and now - events[0] >= self.window:
            events.popleft()
        return events

    def blocked(self, key: str, now: datetime) -> bool:
        return len(self._recent(key, now)) >= self.limit

    def hit(self, key: str, now: datetime) -> None:
        events = self._recent(key, now)
        events.append(now)
        self.events.pop(key, None)
        self.events[key] = events  # al final: la clave más usada hace poco
        while len(self.events) > self.max_keys:
            self.events.pop(next(iter(self.events)))
