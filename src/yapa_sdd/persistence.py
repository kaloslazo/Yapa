"""Guardar y cargar el estado completo en SQLite (iteración 11).

Spec: docs/desarrollo/11-persistencia.md. Cada atributo del repositorio se guarda como JSON
con marcas de tipo ($dec, $dt, $b64, $tuple, $set, $dict, $dc) para no perder precisión ni tipos.
"""

from __future__ import annotations

import base64
import dataclasses
import importlib
import json
import os
import sqlite3
from datetime import datetime
from decimal import Decimal

from .domain import BusinessRuleError
from .store import InMemoryStore


PACKAGE = "yapa_sdd"


def _encode(value):
    if isinstance(value, bool) or value is None or isinstance(value, (int, float, str)):
        return value
    if isinstance(value, Decimal):
        return {"$dec": str(value)}
    if isinstance(value, datetime):
        return {"$dt": value.isoformat()}
    if isinstance(value, bytes):
        return {"$b64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, tuple):
        return {"$tuple": [_encode(item) for item in value]}
    if isinstance(value, set):
        return {"$set": sorted((_encode(item) for item in value), key=json.dumps)}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {"$dict": [[_encode(k), _encode(v)] for k, v in value.items()]}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        cls = type(value)
        fields = {f.name: _encode(getattr(value, f.name)) for f in dataclasses.fields(value)}
        return {"$dc": f"{cls.__module__}.{cls.__qualname__}", "f": fields}
    raise TypeError(f"No se sabe guardar {type(value).__name__}")


def _invalid(detail: str) -> BusinessRuleError:
    return BusinessRuleError("PERSISTENCE_INVALID_DATA", f"La base tiene datos no válidos: {detail}.")


def _class_for(name: str):
    """S-93 / PS-05: solo clases dataclass del propio paquete."""
    module_name, _, class_name = name.rpartition(".")
    if not module_name.startswith(PACKAGE + ".") or not class_name.isidentifier():
        raise _invalid(name)
    try:
        cls = getattr(importlib.import_module(module_name), class_name)
    except (ImportError, AttributeError):
        raise _invalid(name)
    if not (isinstance(cls, type) and dataclasses.is_dataclass(cls)):
        raise _invalid(name)
    return cls


def _decode(value):
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if not isinstance(value, dict):
        return value
    if "$dec" in value:
        return Decimal(value["$dec"])
    if "$dt" in value:
        return datetime.fromisoformat(value["$dt"])
    if "$b64" in value:
        return base64.b64decode(value["$b64"])
    if "$tuple" in value:
        return tuple(_decode(item) for item in value["$tuple"])
    if "$set" in value:
        return {_decode(item) for item in value["$set"]}
    if "$dict" in value:
        return {_decode(k): _decode(v) for k, v in value["$dict"]}
    if "$dc" in value:
        cls = _class_for(value["$dc"])
        fields = {name: _decode(item) for name, item in value.get("f", {}).items()}
        known = {f.name for f in dataclasses.fields(cls)}
        if set(fields) - known:
            raise _invalid(value["$dc"])
        return cls(**fields)
    raise _invalid("objeto sin tipo")


def save(store: InMemoryStore, path: str) -> None:
    """PS-01 y PS-02: todo el estado en una sola transacción."""
    conn = sqlite3.connect(path)
    try:
        with conn:  # commit al final; rollback si algo falla
            conn.execute("CREATE TABLE IF NOT EXISTS estado (clave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
            conn.execute("DELETE FROM estado")
            for key, value in vars(store).items():
                conn.execute("INSERT INTO estado (clave, valor) VALUES (?, ?)", (key, json.dumps(_encode(value))))
    finally:
        conn.close()


def load(path: str) -> InMemoryStore:
    store = InMemoryStore()
    expected = set(vars(store))
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("SELECT clave, valor FROM estado").fetchall()
    finally:
        conn.close()
    for key, raw in rows:
        if key not in expected:
            raise _invalid(key)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            raise _invalid(key)
        setattr(store, key, _decode(data))
    return store


def open_store(path: str) -> InMemoryStore:
    """PS-04: carga la base si existe; si no, la crea con los datos del piloto."""
    if os.path.exists(path):
        return load(path)
    from .seed import pilot_store

    store = pilot_store()
    save(store, path)
    return store
