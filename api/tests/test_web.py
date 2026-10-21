from datetime import datetime
from decimal import Decimal
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
CA01 = {"cant_PAPA-AMARILLA": "5", "cant_CEBOLLA-ROJA": "3", "cant_LIMON": "2", "cant_AJO": "1",
        "cant_LIMPIATODO-GALON": "2"}
PINS = {101: "482915", 105: "739104"}
ADMIN_PASS = "yapa-admin-2026"


class WebSpecTests(unittest.TestCase):
    """Criterios de la iteración 9, ya con acceso (iteración 10)."""

    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        for customer_id, pin in PINS.items():
            set_pin(self.store, customer_id, pin)
        set_admin_password(self.store, "admin-yapa", ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: NOW)
        self.web = WebClient(self.app)
        self.web.login(101, PINS[101])
        self.admin = WebClient(self.app)
        self.admin.login("admin-yapa", ADMIN_PASS, kind="admin")

    def register(self, client=None, code="04512873", amount="59.51"):
        client = client or self.web
        return client.post("/pedidos", dict(CA01, metodo="YAPE", codigo=code, monto=amount, saldo="0"))

    # WA-01
    def test_wa01_catalog_shows_max_price_and_next_tier(self):
        status, _, html = WebClient(self.app).get("/")
        self.assertEqual(status, 200)
        self.assertIn("Papa amarilla", html)
        self.assertIn("S/ 4.03", html)
        self.assertIn("desde 100 kg baja a S/ 3.79", html)
        self.assertNotIn("Plátano de seda", html)

    # WA-02
    def test_wa02_tier_progress(self):
        self.register()
        self.assertIn("5 de 100 kg", self.web.get("/")[2])

    # WA-03
    def test_wa03_quote(self):
        status, _, html = self.web.post("/cotizar", dict(CA01))
        self.assertEqual(status, 200)
        self.assertIn("Total a yapear: S/ 59.51", html)

    # WA-04
    def test_wa04_quote_error(self):
        status, _, html = self.web.post("/cotizar", {"cant_PAPA-AMARILLA": "5", "cant_LIMON": ""})
        self.assertEqual(status, 422)
        self.assertIn("Faltan S/", html)
        self.assertIn("SUBTOTAL_BELOW_MINIMUM", html)

    # WA-05 (ajustado en la iteración 26, S-146)
    def test_wa05_register(self):
        status, _, html = self.register()
        self.assertEqual(status, 200)
        self.assertIn("Pedido 1", html)
        self.assertIn("Registrado", html)
        self.assertEqual(self.store.orders[1].total, Decimal("59.51"))

    # WA-06
    def test_wa06_register_error(self):
        self.register()
        other = WebClient(self.app)
        other.login(105, PINS[105])
        status, _, html = self.register(client=other)
        self.assertEqual(status, 422)
        self.assertIn("PAYMENT_CODE_ALREADY_USED", html)

    # WA-07 (ajustado en la iteración 10)
    def test_wa07_account_of_session(self):
        self.register()
        status, _, html = self.web.get("/cuenta")
        self.assertEqual(status, 200)
        self.assertIn("Pedido 1", html)
        self.assertIn("Saldo: S/ 0.00", html)

    # WA-08 (ajustado en la iteración 26, S-146)
    def test_wa08_cancel_to_balance(self):
        self.register()
        self.admin.post("/admin/verificar", {"pedido": "1"})
        status, _, _ = self.web.post("/cuenta/cancelar", {"pedido": "1", "destino": "SALDO"})
        self.assertEqual(status, 200)
        html = self.web.get("/cuenta")[2]
        self.assertIn("Saldo: S/ 59.51", html)
        self.assertIn("Cancelado", html)

    # WA-09
    def test_wa09_admin_verifies(self):
        self.register()
        self.assertIn("04512873", self.admin.get("/admin")[2])
        self.admin.post("/admin/verificar", {"pedido": "1"})
        self.assertNotIn("04512873", self.admin.get("/admin")[2])

    # WA-10
    def test_wa10_settle_from_web(self):
        for i in range(8):
            customer_id = 700 + i
            self.store.add_customer(Customer(customer_id, f"Vecino {i}", "Z-JM-01"))
            set_pin(self.store, customer_id, "482915")
            client = WebClient(self.app)
            client.login(customer_id, "482915")
            self.register(client=client, code=f"WEB{i}")
            self.admin.post("/admin/verificar", {"pedido": str(i + 1)})
        # HR-10 (iteración 18): liquidar desde la web usa close_cycle; sin entregar la zona, no se liquida.
        # El camino completo (armar, entregar y liquidar) está en test_web_hardening.test_ha10_*.
        status, _, html = self.admin.post("/admin/liquidar", {"ciclo": "2026-W38"})
        self.assertEqual(status, 422)
        self.assertIn("ZONES_PENDING", html)
        self.assertIn("Z-JM-01", html)

    # WA-11 (ajustado en la iteración 10)
    def test_wa11_html_is_escaped(self):
        self.store.add_customer(Customer(666, "<script>alert(1)</script>", "Z-LINCE-01"))
        set_pin(self.store, 666, "482915")
        client = WebClient(self.app)
        client.login(666, "482915")
        html = client.get("/cuenta")[2]
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    # WA-12 (ajustado en la iteración 10)
    def test_wa12_bad_routes_and_data(self):
        self.assertEqual(self.web.get("/no-existe")[0], 404)
        self.assertEqual(self.web.get("/pedidos")[0], 405)
        status, _, html = self.web.post("/cotizar", dict(CA01, **{"cant_PAPA-AMARILLA": "abc"}))
        self.assertEqual(status, 422)
        self.assertIn("INVALID_QUANTITY", html)

    # WA-13
    def test_wa13_mobile_viewport_everywhere(self):
        self.register()
        pages = [self.web.get("/"), self.web.get("/cuenta"), self.admin.get("/admin"),
                 self.web.post("/cotizar", dict(CA01)), WebClient(self.app).get("/entrar")]
        for status, _, html in pages:
            with self.subTest(status=status):
                self.assertIn('<meta name="viewport"', html)


if __name__ == "__main__":
    unittest.main()
