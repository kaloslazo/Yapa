import io
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode
from wsgiref.util import setup_testing_defaults
import unittest

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
CA01 = {"cant_PAPA-AMARILLA": "5", "cant_CEBOLLA-ROJA": "3", "cant_LIMON": "2", "cant_AJO": "1",
        "cant_LIMPIATODO-GALON": "2"}


def call(app, method, path, data=None):
    environ = {}
    setup_testing_defaults(environ)
    path, _, query = path.partition("?")
    body = urlencode(data or {}).encode("utf-8")
    environ.update({
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(body)),
        "wsgi.input": io.BytesIO(body),
    })
    result = {}

    def start_response(status, headers):
        result["status"] = int(status.split()[0])

    html = b"".join(app(environ, start_response)).decode("utf-8")
    return result["status"], html


class WebSpecTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()
        self.app = create_app(self.store, clock=lambda: NOW)

    def register(self, code="04512873", customer="101", amount="59.51", **extra):
        data = dict(CA01, cliente=customer, metodo="YAPE", codigo=code, monto=amount, saldo="0")
        data.update(extra)
        return call(self.app, "POST", "/pedidos", data)

    # WA-01
    def test_wa01_catalog_shows_max_price_and_next_tier(self):
        status, html = call(self.app, "GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Papa amarilla", html)
        self.assertIn("S/ 4.03", html)
        self.assertIn("desde 100 kg baja a S/ 3.79", html)
        self.assertNotIn("Plátano de seda", html)

    # WA-02
    def test_wa02_tier_progress(self):
        self.register()
        status, html = call(self.app, "GET", "/")
        self.assertIn("5 de 100 kg", html)

    # WA-03
    def test_wa03_quote(self):
        status, html = call(self.app, "POST", "/cotizar", dict(CA01, cliente="101"))
        self.assertEqual(status, 200)
        self.assertIn("Total a yapear: S/ 59.51", html)

    # WA-04
    def test_wa04_quote_error(self):
        status, html = call(self.app, "POST", "/cotizar", {"cliente": "101", "cant_PAPA-AMARILLA": "5",
                                                           "cant_LIMON": ""})
        self.assertEqual(status, 422)
        self.assertIn("Faltan S/", html)
        self.assertIn("SUBTOTAL_BELOW_MINIMUM", html)

    # WA-05
    def test_wa05_register(self):
        status, html = self.register()
        self.assertEqual(status, 200)
        self.assertIn("Pedido 1", html)
        self.assertIn("REGISTRADO", html)
        self.assertEqual(self.store.orders[1].total, Decimal("59.51"))

    # WA-06
    def test_wa06_register_error(self):
        self.register()
        status, html = self.register(customer="105")
        self.assertEqual(status, 422)
        self.assertIn("PAYMENT_CODE_ALREADY_USED", html)

    # WA-07
    def test_wa07_account(self):
        self.register()
        status, html = call(self.app, "GET", "/cuenta?cliente=101")
        self.assertEqual(status, 200)
        self.assertIn("Pedido 1", html)
        self.assertIn("Saldo: S/ 0.00", html)
        status, _ = call(self.app, "GET", "/cuenta?cliente=999")
        self.assertEqual(status, 404)

    # WA-08
    def test_wa08_cancel_to_balance(self):
        self.register()
        call(self.app, "POST", "/admin/verificar", {"pedido": "1"})
        status, html = call(self.app, "POST", "/cuenta/cancelar", {"cliente": "101", "pedido": "1", "destino": "SALDO"})
        self.assertEqual(status, 200)
        status, html = call(self.app, "GET", "/cuenta?cliente=101")
        self.assertIn("Saldo: S/ 59.51", html)
        self.assertIn("CANCELADO_POR_CLIENTE", html)

    # WA-09
    def test_wa09_admin_verifies(self):
        self.register()
        status, html = call(self.app, "GET", "/admin")
        self.assertIn("04512873", html)
        call(self.app, "POST", "/admin/verificar", {"pedido": "1"})
        status, html = call(self.app, "GET", "/admin")
        self.assertNotIn("04512873", html)

    # WA-10
    def test_wa10_settle_from_web(self):
        for i in range(8):
            customer_id = 700 + i
            self.store.add_customer(Customer(customer_id, f"Vecino {i}", "Z-JM-01"))
            self.register(code=f"WEB{i}", customer=str(customer_id))
            call(self.app, "POST", "/admin/verificar", {"pedido": str(i + 1)})
        status, html = call(self.app, "POST", "/admin/liquidar", {"ciclo": "2026-W38"})
        self.assertEqual(status, 200)
        self.assertIn("LIQUIDADO", html)
        self.assertIn("PAPA-AMARILLA", html)

    # WA-11
    def test_wa11_html_is_escaped(self):
        self.store.add_customer(Customer(666, "<script>alert(1)</script>", "Z-LINCE-01"))
        status, html = call(self.app, "GET", "/cuenta?cliente=666")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    # WA-12
    def test_wa12_bad_routes_and_data(self):
        self.assertEqual(call(self.app, "GET", "/no-existe")[0], 404)
        self.assertEqual(call(self.app, "GET", "/pedidos")[0], 405)
        status, html = call(self.app, "POST", "/cotizar", dict(CA01, cliente="abc"))
        self.assertEqual(status, 422)
        status, html = call(self.app, "GET", "/cuenta?cliente=abc")
        self.assertEqual(status, 404)

    # WA-13
    def test_wa13_mobile_viewport_everywhere(self):
        self.register()
        for method, path, data in (("GET", "/", None), ("GET", "/cuenta?cliente=101", None), ("GET", "/admin", None),
                                   ("POST", "/cotizar", dict(CA01, cliente="101"))):
            with self.subTest(path=path):
                self.assertIn('<meta name="viewport"', call(self.app, method, path, data)[1])


if __name__ == "__main__":
    unittest.main()
