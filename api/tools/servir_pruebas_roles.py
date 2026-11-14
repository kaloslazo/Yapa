"""Demo efímera para probar fotos y rutas; no abre ni modifica bases existentes."""
import argparse
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'api/src'))
from yapa_sdd.demo import demo_store, DEMO_NOW, _order, BASKETS
from yapa_sdd.domain import Customer
from yapa_sdd.order_registration import verify_payment
from yapa_sdd.web.__main__ import _demo_credentials
from yapa_sdd.web.api import create_api
from yapa_sdd.web.app import create_app
from yapa_sdd.web import produccion

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--puerto', type=int, default=8010)
args = parser.parse_args()
store = demo_store()
next_customer = 9000
for zone in ('Z-LINCE-01', 'Z-JM-01', 'Z-LINCE-03'):
    existing = [o for o in store.orders_in_cycle('2026-W40') if o.zone_id == zone]
    for index in range(max(0, 8 - len(existing))):
        next_customer += 1
        store.add_customer(Customer(next_customer, f'Vecino de prueba {next_customer}', zone))
        _order(store, next_customer, BASKETS[index % len(BASKETS)], DEMO_NOW)
for order in store.orders_in_cycle('2026-W40'):
    if order.payment_status != 'VERIFICADO':
        verify_payment(store, order.order_id, now=DEMO_NOW)
_demo_credentials(store)
clock = lambda: DEMO_NOW + timedelta(days=1)  # jueves 01/10, después del cierre
with tempfile.TemporaryDirectory(prefix='yapa-pruebas-fotos-') as photos:
    api = create_api(store, clock=clock, photo_dir=photos)
    html = create_app(store, clock=clock, photo_dir=photos)
    app = produccion.locked(produccion.compose(api, html, str(ROOT / 'dist')))
    print(f'Demo en memoria: http://127.0.0.1:{args.puerto}. 3 zonas con pedidos de prueba verificados; no son pagos reales.', flush=True)
    with make_server('127.0.0.1', args.puerto, app, server_class=produccion.ThreadedServer) as server:
        server.serve_forever()
