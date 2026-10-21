"""Servidor de demo: PYTHONPATH=src python -m yapa_sdd.web [--puerto 8000] [--ahora 2026-09-16T10:00:00-05:00] [--demo]"""

import argparse
import os
import sys
from datetime import datetime
from wsgiref.simple_server import make_server

from .. import auth, persistence
from ..demo import DEMO_NOW, demo_store
from ..domain import BusinessRuleError
from ..seed import pilot_store
from ..google_identity import google_from_env
from ..mailer import mailer_from_env
from .api import create_api
from .app import create_app
from . import produccion


DEMO_PINS = {101: "482915", 105: "739104", 116: "260318"}
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
    parser.add_argument("--escuchar", default=produccion.LOCAL, help="dirección donde escucha (S-231); 0.0.0.0 abre el servidor y exige --base")
    parser.add_argument("--estaticos", help="carpeta de la web construida (npm run build -> dist), S-234")
    parser.add_argument("--demo", action="store_true", help="arranca con una semana de demo ya vivida (PW-08)")
    args = parser.parse_args()
    if args.demo and args.base:  # S-143
        parser.error("--demo trabaja en memoria; no se combina con --base")
    try:
        produccion.check_listen(args.escuchar, args.base)  # S-231
    except BusinessRuleError as error:
        parser.error(str(error))
    clock = None
    if args.ahora or args.demo:
        fixed = datetime.fromisoformat(args.ahora) if args.ahora else DEMO_NOW
        clock = lambda: fixed  # noqa: E731
    on_change = None
    if args.demo:
        store = demo_store()
        print("Semana de demo: 2026-W39 entregada y liquidada, 2026-W40 abierta (miércoles 30/09, 10:00)")
    elif args.base:
        store = persistence.open_store(args.base)
        on_change = lambda s: persistence.save(s, args.base)  # noqa: E731
    else:
        store = pilot_store()
    if args.base and not args.demo:  # S-228: modo servidor, sin credenciales de demo
        try:
            produccion.prepare_server_credentials(store, os.environ)
        except BusinessRuleError as error:
            sys.exit(f"No se puede arrancar: {error}")
    else:
        _demo_credentials(store)
    if args.base:
        persistence.save(store, args.base)
    html = create_app(store, clock, on_change=on_change)
    api = create_api(store, clock, on_change=on_change, mailer=mailer_from_env(), google=google_from_env(),
                     secure_cookie=produccion.secure_cookie(os.environ))  # S-153: la API JSON en /api del mismo servidor

    app = produccion.locked(produccion.compose(api, html, args.estaticos))  # S-232, S-233, S-234
    with make_server(args.escuchar, args.puerto, app, server_class=produccion.ThreadedServer) as server:  # S-61, S-231
        print(f"Yapa en http://{args.escuchar}:{args.puerto}  (Ctrl+C para salir)")
        server.serve_forever()


if __name__ == "__main__":
    main()
