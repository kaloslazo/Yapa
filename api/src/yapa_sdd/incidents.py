"""Incidencias que registra atención; no mueven dinero (iteración 56, S-300).

Spec: docs/desarrollo/56-compra-real-y-armado.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from . import partners
from .domain import BusinessRuleError
from .fulfillment import check_role
from .store import InMemoryStore


KINDS = frozenset({"ENTREGA", "BOLSA", "TRATO", "OTRO"})  # S-300
MAX_TEXT = 500


@dataclass
class Incident:
    incident_id: int
    order_id: int
    kind: str
    description: str
    opened_by: str
    opened_at: datetime
    status: str = "ABIERTA"
    note: str = ""
    closed_by: str = ""
    closed_at: datetime | None = None


def _text(value) -> str:
    text = str(value or "").strip()
    if not text or len(text) > MAX_TEXT:
        raise BusinessRuleError("INVALID_INCIDENT", f"Escribe entre 1 y {MAX_TEXT} caracteres.")
    return text


def open_incident(store: InMemoryStore, order_id: int, kind: str, description, *, by, now: datetime) -> Incident:
    check_role(store, by, partners.SUPPORT)  # IN-01
    if order_id not in store.orders:  # IN-02
        raise BusinessRuleError("ORDER_NOT_FOUND", "El pedido no existe.")
    if kind not in KINDS:
        raise BusinessRuleError("INVALID_INCIDENT", "Elige si es de la entrega, la bolsa, el trato u otra cosa.")
    incident = Incident(store._next_incident_id, order_id, kind, _text(description), by, now)
    store.incidents[incident.incident_id] = incident
    store._next_incident_id += 1
    return incident


def close_incident(store: InMemoryStore, incident_id: int, note, *, by, now: datetime) -> Incident:
    check_role(store, by, partners.SUPPORT)  # IN-01
    incident = store.incidents.get(incident_id)
    if incident is None:  # IN-03
        raise BusinessRuleError("INCIDENT_NOT_FOUND", "La incidencia no existe.")
    if incident.status != "ABIERTA":
        raise BusinessRuleError("INCIDENT_ALREADY_CLOSED", "La incidencia ya está cerrada.")
    incident.note = _text(note)
    incident.status = "CERRADA"
    incident.closed_by = by
    incident.closed_at = now
    return incident
