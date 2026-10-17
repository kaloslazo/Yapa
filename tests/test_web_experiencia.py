"""Iteración 26: experiencia de compra (docs/desarrollo/26-experiencia-compra.md)."""

from datetime import date, datetime
from decimal import Decimal as D
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd import reference, wallet
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
DEMO_NOW = datetime(2026, 9, 30, 10, 0, tzinfo=LIMA)
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
BASKET = {"cant_PAPA-AMARILLA": "5", "cant_PAPA-BLANCA": "10", "cant_CEBOLLA-ROJA": "10"}  # S/ 61.00


class ShoppingExperienceSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: NOW)
        self.web = WebClient(self.app)
        self.web.login(101, PIN)
        self.admin = WebClient(self.app)
        self.admin.login(ADMIN, ADMIN_PASS, kind="admin")

    def register(self):
        return self.web.post("/pedidos", dict(BASKET, metodo="YAPE", codigo="OP-1", monto="61.00", saldo="0"))

    # EC-A
    def test_ec_a_catalog_buttons_and_cart_bar(self):
        html = self.web.get("/")[2]
        self.assertIn('data-step="0.25"', html)
        self.assertIn('aria-label="Quitar uno de Ajo criollo"', html)
        self.assertIn('aria-label="Agregar uno de Ajo criollo"', html)
        self.assertIn('id="carrito"', html)
        self.assertIn('data-minimo="50.00"', html)
        self.assertNotIn('id="carrito"', WebClient(self.app).get("/")[2])

    # EC-B
    def test_ec_b_cart_page(self):
        status, _, html = self.web.post("/cotizar", dict(BASKET))
        self.assertEqual(status, 200)
        self.assertIn("Tu carrito", html)
        for name in ("Papa amarilla", "Papa blanca", "Cebolla roja"):
            self.assertIn(name, html)
        self.assertIn("Total a yapear: S/ 61.00", html)
        self.assertIn('action="/pedidos"', html)
        self.assertIn('<input type="hidden" name="cant_PAPA-AMARILLA" value="5">', html)

    # EC-C
    def test_ec_c_cart_savings(self):
        reference.register_reference(self.store, "PAPA-AMARILLA", "SUPERMERCADO", D("7.99"), "Plaza Vea",
                                     date(2026, 9, 15), by=ADMIN, now=NOW)
        html = self.web.post("/cotizar", dict(BASKET))[2]
        self.assertIn("frente al supermercado", html)
        self.assertIn("S/ 19.79", html)

    # EC-D
    def test_ec_d_balance_is_proposed(self):
        wallet.credit(self.store, 101, D("10.00"), "AJUSTE_PRUEBA", NOW)
        html = self.web.post("/cotizar", dict(BASKET))[2]
        self.assertIn('name="saldo" inputmode="decimal" value="10.00"', html)
        self.assertIn('name="monto" inputmode="decimal" value="51.00"', html)

    # EC-E
    def test_ec_e_confirmation(self):
        status, _, html = self.register()
        self.assertEqual(status, 200)
        for text in ("Ana", "Pedido 1", "Registrado", "sábado"):
            self.assertIn(text, html)

    # EC-F
    def test_ec_f_cancel_with_buttons(self):
        self.register()
        html = self.web.get("/cuenta")[2]
        self.assertIn('<input type="hidden" name="pedido" value="1">', html)
        self.assertIn('name="destino" value="MEDIO_DE_PAGO"', html)
        self.assertIn('name="destino" value="SALDO"', html)
        self.assertNotIn('<input name="pedido">', html)
        self.assertEqual(self.web.post("/cuenta/cancelar", {"pedido": "1", "destino": "SALDO"})[0], 200)
        html = self.web.get("/cuenta")[2]
        self.assertIn("Cancelado", html)
        self.assertNotIn('action="/cuenta/cancelar"', html)

    # EC-H
    def test_ec_h_admin_dashboard(self):
        self.register()
        html = self.admin.get("/admin")[2]
        self.assertRegex(html, r"Pedidos de la semana</span><strong>1</strong>")
        self.assertRegex(html, r"Por verificar</span><strong>1</strong>")
        self.assertIn('<select name="ciclo">', html)
        self.assertIn('<option value="2026-W38"', html)

    # EC-I
    def test_ec_i_messages(self):
        self.register()
        status, _, html = self.admin.post("/admin/verificar", {"pedido": "1"})
        self.assertEqual(status, 200)
        self.assertIn('class="card ok"', html)
        status, _, html = self.web.get("/no-existe")
        self.assertEqual(status, 404)
        self.assertNotIn('class="card ok"', html)
        status, _, html = self.web.post("/cotizar", {"cant_AJO": "1"})
        self.assertEqual(status, 422)
        self.assertIn("SUBTOTAL_BELOW_MINIMUM", html)
        self.assertIn("Volver", html)


class DemoSavingsSpecTests(unittest.TestCase):
    # EC-G
    def test_ec_g_total_savings_in_account(self):
        fast_hashing(self)
        from yapa_sdd.demo import demo_store

        store = demo_store()
        set_pin(store, 101, PIN)
        web = WebClient(create_app(store, clock=lambda: DEMO_NOW))
        web.login(101, PIN)
        self.assertIn("Ahorraste S/ 42.31 frente al supermercado", web.get("/cuenta")[2])


if __name__ == "__main__":
    unittest.main()
