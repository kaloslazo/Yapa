"""Demo de la semana completa con un reloj que se mueve sin reiniciar: python api/tools/demo_semana.py [--puerto 8010]

Arranca como servir_demo.py (semana anterior ya liquidada, esta semana abierta el miércoles a las 10:00 y las
cuentas de prueba de todos los roles), pero el reloj del negocio se mueve desde /api/demo/reloj:
miércoles (pedidos y pagos), jueves (compra), viernes (armado), sábado (reparto y portería),
domingo (reclamos y liquidación) y la semana siguiente (usar el saldo). Solo para uso local.
"""

import argparse
import html
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yapa_sdd import ia, invitations  # noqa: E402
from yapa_sdd.cycle import LIMA, cycle_id, is_open  # noqa: E402
from yapa_sdd.demo import _order, demo_store  # noqa: E402
from yapa_sdd.google_identity import google_from_env  # noqa: E402
from yapa_sdd.mailer import mailer_from_env  # noqa: E402
from yapa_sdd.web import produccion  # noqa: E402
from yapa_sdd.web.__main__ import _demo_credentials  # noqa: E402
from yapa_sdd.web.api import create_api  # noqa: E402
from yapa_sdd.web.app import create_app  # noqa: E402

# momento -> (cuánto después del miércoles 10:00 de la demo, qué se muestra)
MOMENTOS = {
    "miercoles": (timedelta(0), "Miércoles 10:00 · los vecinos piden y pagan, el equipo verifica"),
    "jueves": (timedelta(days=1), "Jueves 10:00 · cerró el pedido: compras registra lo que llegó y el flete"),
    "viernes": (timedelta(days=2), "Viernes 10:00 · armado: foto de cada bolsa"),
    "sabado": (timedelta(days=3), "Sábado 10:00 · reparto sale, entrega con foto y la portería recibe"),
    "domingo": (timedelta(days=3, hours=23), "Domingo 09:00 · reclamos (dentro de las 24 h) y liquidación"),
    "siguiente": (timedelta(days=7), "Miércoles siguiente 10:00 · semana nueva: el vecino usa su saldo"),
}
RUTA = "/api/demo/reloj"
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

# dos vecinos de Los Álamos ya pidieron lejía: van 10 de 12 galones, así que si Ana pide 2 o más la lejía
# baja de tramo para todos y en la liquidación se ve el "te devolvemos" (sin esto nadie cruza un tramo)
PEDIDOS_EXTRA = {
    111: {"LEJIA-GALON": "6", "PAPA-AMARILLA": "5"},
    112: {"LEJIA-GALON": "4", "PAPA-AMARILLA": "8"},
}


def momento(base: datetime, nombre: str) -> datetime:
    return base + MOMENTOS[nombre][0]


def con_reloj(app, reloj: dict, base: datetime):
    """Atiende /api/demo/reloj (página con un enlace por momento) y deja pasar todo lo demás."""
    def wrapped(environ, start_response):
        if environ.get("PATH_INFO", "").rstrip("/") != RUTA:
            return app(environ, start_response)
        ir = parse_qs(environ.get("QUERY_STRING", "")).get("ir", [""])[0]
        if ir in MOMENTOS:
            reloj["ahora"] = momento(base, ir)
            print(f"Reloj de la demo: {DIAS[reloj['ahora'].weekday()]} {reloj['ahora']:%d/%m %H:%M}")
        ahora = reloj["ahora"]
        estado = "abierto" if is_open(ahora) else "cerrado"
        enlaces = "".join(
            f'<li><a href="?ir={nombre}"{" class=actual" if momento(base, nombre) == ahora else ""}>{html.escape(texto)}</a></li>'
            for nombre, (_, texto) in MOMENTOS.items())
        cuerpo = (f"<!doctype html><meta charset=utf-8><title>Reloj de la demo</title>"
                  "<style>body{font:16px system-ui;margin:32px;max-width:620px}a{color:#111}"
                  "li{margin:10px 0}.actual{font-weight:700}</style>"
                  f"<h1>Reloj de la demo</h1><p>Ahora: <b>{DIAS[ahora.weekday()]} {ahora:%d/%m %H:%M}</b> · ciclo {cycle_id(ahora)} {estado}</p>"
                  f"<ol>{enlaces}</ol><p>Después de mover el reloj, recarga la tienda.</p>").encode()
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])
        return [cuerpo]
    return wrapped


def armar(now: datetime, credenciales: bool = True):
    """La semana de demo de `now` (la anterior liquidada, esta abierta) con los dos pedidos de lejía."""
    store = demo_store(now)
    if credenciales:
        _demo_credentials(store)
    for customer_id, basket in PEDIDOS_EXTRA.items():
        _order(store, customer_id, basket, store.demo_now)
    return store


def main() -> None:
    parser = argparse.ArgumentParser(description="Yapa · demo de la semana completa con reloj movible")
    parser.add_argument("--puerto", type=int, default=8010)
    args = parser.parse_args()
    store = armar(datetime.now(LIMA))
    base = store.demo_now
    reloj = {"ahora": base}
    clock = lambda: reloj["ahora"]  # noqa: E731
    secure = produccion.secure_cookie(os.environ)
    api = create_api(store, clock, mailer=mailer_from_env(server=False), google=google_from_env(), secure_cookie=secure,
                     security_clock=lambda: datetime.now(LIMA), payee=produccion.payee(os.environ, demo=True),
                     ai=ia.from_env(os.environ))
    app = produccion.locked(produccion.compose(api, create_app(store, clock), None,
                                               lambda code: invitations.preview(store, code), secure=secure))
    with make_server("127.0.0.1", args.puerto, con_reloj(app, reloj, base), server_class=produccion.ThreadedServer) as server:
        print(f"Yapa en http://127.0.0.1:{args.puerto}  ·  reloj en http://127.0.0.1:{args.puerto}{RUTA}  (Ctrl+C para salir)")
        server.serve_forever()


if __name__ == "__main__":
    main()
