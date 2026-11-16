"""Demo de la semana completa con un reloj que se mueve sin reiniciar: python api/tools/demo_semana.py [--puerto 8010]

Arranca como servir_demo.py (semana anterior ya liquidada, esta semana abierta el miércoles a las 10:00 y las
cuentas de prueba de todos los roles), pero el reloj del negocio se mueve desde /api/demo/reloj:
miércoles (pedidos y pagos), jueves (compra), viernes (armado), sábado (reparto y portería),
domingo (reclamos y liquidación) y la semana siguiente (usar el saldo). Solo para uso local.
"""

import argparse
import hashlib
import html
import os
import shutil
import sys
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yapa_sdd import catalog, claims, customers, fulfillment, ia, incidents, invitations, logistics, purchase, supplier_offers  # noqa: E402
from yapa_sdd.cycle import opens_at  # noqa: E402
from yapa_sdd.cycle import add_weeks  # noqa: E402
from decimal import Decimal as D  # noqa: E402
from yapa_sdd.domain import Customer  # noqa: E402
from yapa_sdd.order_registration import verify_payment  # noqa: E402
from yapa_sdd.cycle import LIMA, cycle_id, is_open  # noqa: E402
from yapa_sdd.demo import BASKETS, _order, demo_store  # noqa: E402
from yapa_sdd.google_identity import google_from_env  # noqa: E402
from yapa_sdd.mailer import mailer_from_env  # noqa: E402
from yapa_sdd.web import produccion  # noqa: E402
from yapa_sdd.web.__main__ import _demo_credentials  # noqa: E402
from yapa_sdd.web.api import PHOTO_PATH, create_api  # noqa: E402
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


# vecinos de prueba para que la semana tenga varios edificios que llegan al mínimo (y una ruta de verdad)
VECINOS_EXTRA = {
    "Z-LINCE-02": ["Gloria Huerta", "Óscar Linares", "Patricia Cueva"],
    "Z-JM-01": ["Hugo Benavides", "Silvia Ponce", "Andrés Tello", "Karina Soto", "Mario Gálvez", "Nora Villa"],
    "Z-LINCE-03": ["Iván Ríos", "Lorena Campos", "Fabio Ortiz", "Celia Muñoz", "Diego Arce", "Vilma Rojas", "Ernesto Paz", "Rubén Salas"],
}
SIN_VERIFICAR = {"Z-LINCE-02"}
RECIBEN = {"Z-LINCE-02": "Conserje Las Palmeras", "Z-JM-01": "Recepción San Felipe", "Z-LINCE-03": "Portería Arenales"}  # quedan pagos por verificar para mostrarlo en el Resumen


def armar(now: datetime, credenciales: bool = True, completa: bool = True):
    """La semana de demo de `now` (la anterior liquidada, esta abierta) con los dos pedidos de lejía.
    Con `completa`, también la semana poblada para probar cada módulo (ver `poblar`)."""
    store = demo_store(now)
    if credenciales:
        _demo_credentials(store)
    for customer_id, basket in PEDIDOS_EXTRA.items():
        _order(store, customer_id, basket, store.demo_now)
    if completa:
        poblar(store, credenciales)
    return store


# historia: las 5 semanas antes de la ya liquidada, para que la app se vea con semanas de uso real.
# Los Álamos desde el inicio; Las Palmeras se suma en la tercera; San Felipe no llega al mínimo la primera semana
# (se le devuelve todo) y desde la segunda sí; Arenales es nuevo esta semana. Un reclamo aprobado en la cuarta.
ALAMOS = [101, 105, 106, 107, 108, 109, 110, 111, 112]
SEMANAS_ATRAS = (6, 5, 4, 3, 2)


def historial(store, ahora, nuevos: dict) -> None:
    hechas = []
    for k, atras in enumerate(SEMANAS_ATRAS):
        semana = add_weeks(cycle_id(ahora), -atras)
        miercoles = opens_at(semana) + timedelta(days=2, hours=10)
        sabado = miercoles + timedelta(days=3)
        quienes = ALAMOS[:8 + min(k, 1)] + nuevos.get("Z-LINCE-02", [])[:max(0, k - 1)]
        quienes += [113, 114] + nuevos.get("Z-JM-01", [])[:2 if k == 0 else 6]
        for i, cliente in enumerate(quienes):
            orden = _order(store, cliente, BASKETS[(i + k) % len(BASKETS)], miercoles)
            verify_payment(store, orden.order_id, now=miercoles)
        ordenes = store.orders_in_cycle(semana)
        atendidas = [o for o in ordenes if fulfillment.is_attended(store, o)]
        for orden in atendidas:
            fulfillment.pack_bag(store, orden.order_id, by="admin-yapa", photo=f"fotos/h{k}-pedido-{orden.order_id}.jpg",
                                 now=sabado - timedelta(days=1))
        purchase.register_purchase(store, semana, {}, by="admin-yapa", now=miercoles + timedelta(days=1))
        logistics.register_freight(store, semana, "Fletes Santa Anita", D(str(110 + 5 * k)), by="admin-yapa",
                                   now=miercoles + timedelta(days=1))
        for zona in sorted({o.zone_id for o in atendidas}):
            z = store.zones[zona]
            logistics.dispatch_zone(store, semana, zona, by="admin-yapa", now=sabado)
            fulfillment.deliver_zone(store, semana, zona, by="admin-yapa", photo=f"fotos/h{k}-entrega-{zona}.jpg",
                                     received_by=z.reception_contact or "Recepción", now=sabado + timedelta(hours=1))
        reclamo = None
        if k == 3:
            orden = next(o for o in atendidas if any(l.product_id == "CEBOLLA-ROJA" for l in o.lines))
            reclamo = claims.file_claim(store, orden.order_id, customer_id=orden.customer_id, product_id="CEBOLLA-ROJA",
                                        quantity="1", reason="DANADO", photo=f"fotos/h{k}-reclamo.jpg",
                                        now=sabado + timedelta(hours=8))
        fulfillment.close_cycle(store, semana, at=sabado + timedelta(hours=23))
        if reclamo is not None:
            claims.review_claim(store, reclamo.claim_id, by="admin-yapa", approve=True, now=sabado + timedelta(days=1))
        hechas.append(semana)
    for clave in [c for c in store.demand_history if c[0] in hechas]:  # la historia real reemplaza a la sembrada
        del store.demand_history[clave]


def poblar(store, credenciales: bool) -> None:
    """Datos de prueba para el video: más edificios que llegan al mínimo (compras, armado, reparto con mapa y portería),
    pagos por verificar, la lista del proveedor esperando aprobación, una incidencia abierta y un pedido de PIN."""
    ahora = store.demo_now
    for zona, contacto in RECIBEN.items():  # cada edificio con quién recibe, para que el reparto pueda entregar
        z = store.zones[zona]
        z.reception_kind, z.reception_contact = z.reception_kind or "PORTERIA", z.reception_contact or contacto
    numero = max(store.customers) + 1
    nuevos: dict[str, list[int]] = {}
    for zona, nombres in VECINOS_EXTRA.items():
        z = store.zones[zona]
        for nombre in nombres:
            store.add_customer(Customer(numero, nombre, zona, lat=z.lat, lon=z.lon))
            nuevos.setdefault(zona, []).append(numero)
            numero += 1
    historial(store, ahora, nuevos)
    for zona, clientes in nuevos.items():
        for i, cliente in enumerate(clientes):
            orden = _order(store, cliente, BASKETS[(cliente + i) % len(BASKETS)], ahora)
            if zona not in SIN_VERIFICAR or i == 0:
                verify_payment(store, orden.order_id, now=ahora)
    for orden in store.orders_in_cycle(cycle_id(ahora)):  # San Felipe: los dos vecinos que ya tenía también pagan
        if orden.zone_id == "Z-JM-01" and orden.payment_status != "VERIFICADO":
            verify_payment(store, orden.order_id, now=ahora)
    for cliente in (113, 114):
        if store.find_order(cliente, cycle_id(ahora)) is None:
            orden = _order(store, cliente, BASKETS[cliente % len(BASKETS)], ahora)
            verify_payment(store, orden.order_id, now=ahora)
    if not credenciales:
        return
    proveedor = "frescos-demo"
    proxima = add_weeks(cycle_id(ahora), 1)
    lista = catalog.export_catalog(p for p in store.catalog_for(proxima).values() if p.supplier_id == "SUP-FRESCOS")
    lista = lista.replace(",3.60", ",3.40").replace(",1.90", ",1.80")  # baja dos precios: el admin lo ve en Propuestas
    try:
        supplier_offers.submit_offer(store, proxima, lista, by=proveedor, now=ahora)
    except Exception as error:  # la demo sigue aunque cambie el catálogo
        print(f"(demo) sin propuesta del proveedor: {error}")
    pasada = next((o for o in store.orders.values() if o.cycle == add_weeks(cycle_id(ahora), -1)), None)
    if pasada is not None:
        incidents.open_incident(store, pasada.order_id, "ENTREGA",
                                "La vecina dice que la bolsa llegó con la cebolla suelta; revisar con armado.",
                                by="atencion-demo", now=ahora)
    customers.request_pin_help(store, 114, ahora)


def fotos_de_la_semilla(store, carpeta: str = "fotos") -> None:
    """La semilla guarda nombres como fotos/w39-pedido-1.jpg, que el motor no sirve (S-180): les pone una foto real."""
    productos = Path(__file__).resolve().parents[2] / "public" / "images" / "products"
    destino = Path(carpeta)
    destino.mkdir(exist_ok=True)

    def real(ruta: str, origen: str) -> str:
        if not ruta or PHOTO_PATH.fullmatch(ruta):
            return ruta
        nombre = hashlib.sha256(ruta.encode()).hexdigest()[:16] + ".webp"
        shutil.copyfile(productos / origen, destino / nombre)
        return f"fotos/{nombre}"

    for order_id, bags in store.bags.items():
        store.bags[order_id] = [replace(bag, photo=real(bag.photo, "papa-amarilla.webp")) for bag in bags]
    for key, delivery in store.deliveries.items():
        store.deliveries[key] = replace(delivery, photo=real(delivery.photo, "cebolla-roja.webp"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Yapa · demo de la semana completa con reloj movible")
    parser.add_argument("--puerto", type=int, default=8010)
    args = parser.parse_args()
    store = armar(datetime.now(LIMA))
    fotos_de_la_semilla(store)
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
