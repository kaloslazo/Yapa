"""Servidor de demo: PYTHONPATH=src python -m yapa_sdd.web [--puerto 8000] [--ahora 2026-09-16T10:00:00-05:00]"""

import argparse
from datetime import datetime
from wsgiref.simple_server import make_server

from .. import auth, persistence
from ..seed import pilot_store
from .app import create_app


DEMO_PINS = {101: "482915", 105: "739104"}
DEMO_ADMIN = ("admin-yapa", "yapa-admin-2026")


def _demo_credentials(store) -> None:
    """S-94: si no hay ninguna credencial, crea las de demo (solo para uso local)."""
    if store.credentials:
        return
    for customer_id, pin in DEMO_PINS.items():
        auth.set_pin(store, customer_id, pin)
    auth.set_admin_password(store, *DEMO_ADMIN)
    print("Credenciales de DEMO creadas (cámbialas antes de usar datos reales):")
    for customer_id, pin in DEMO_PINS.items():
        print(f"  vecino {customer_id} · PIN {pin}")
    print(f"  admin {DEMO_ADMIN[0]} · contraseña {DEMO_ADMIN[1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Yapa · interfaz web de demo")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--ahora", help="fija la hora (S-63), p. ej. 2026-09-16T10:00:00-05:00")
    parser.add_argument("--base", help="archivo SQLite donde se guardan los datos (PS-04); sin esto, solo memoria")
    args = parser.parse_args()
    clock = None
    if args.ahora:
        fixed = datetime.fromisoformat(args.ahora)
        clock = lambda: fixed  # noqa: E731
    if args.base:
        store = persistence.open_store(args.base)
        _demo_credentials(store)
        persistence.save(store, args.base)
        app = create_app(store, clock, on_change=lambda s: persistence.save(s, args.base))
    else:
        store = pilot_store()
        _demo_credentials(store)
        app = create_app(store, clock)
    with make_server("127.0.0.1", args.puerto, app) as server:  # S-61: solo esta máquina
        print(f"Yapa en http://127.0.0.1:{args.puerto}  (Ctrl+C para salir)")
        server.serve_forever()


if __name__ == "__main__":
    main()
