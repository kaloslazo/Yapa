"""Servidor de demo: PYTHONPATH=src python -m yapa_sdd.web [--puerto 8000] [--ahora 2026-09-16T10:00:00-05:00]"""

import argparse
from datetime import datetime
from wsgiref.simple_server import make_server

from ..seed import pilot_store
from .app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Yapa · interfaz web de demo")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--ahora", help="fija la hora (S-42), p. ej. 2026-09-16T10:00:00-05:00")
    args = parser.parse_args()
    clock = None
    if args.ahora:
        fixed = datetime.fromisoformat(args.ahora)
        clock = lambda: fixed  # noqa: E731
    app = create_app(pilot_store(), clock)
    with make_server("127.0.0.1", args.puerto, app) as server:  # S-40: solo esta máquina
        print(f"Yapa en http://127.0.0.1:{args.puerto}  (Ctrl+C para salir)")
        server.serve_forever()


if __name__ == "__main__":
    main()
