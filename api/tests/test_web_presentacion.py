"""Iteración 25: presentación de la web y semana de demo (docs/desarrollo/25-presentacion-web.md)."""

from datetime import date, datetime
from decimal import Decimal as D
import re
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd import reference
from yapa_sdd.audit import money_balance
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
DEMO_NOW = datetime(2026, 9, 30, 10, 0, tzinfo=LIMA)
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
BASKET = {"cant_PAPA-AMARILLA": "5", "cant_PAPA-BLANCA": "10", "cant_CEBOLLA-ROJA": "10"}  # S/ 61.00


class PresentationSpecTests(unittest.TestCase):
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

    def supermarket(self, price):
        reference.register_reference(self.store, "PAPA-AMARILLA", "SUPERMERCADO", D(price), "Plaza Vea",
                                     date(2026, 9, 15), by=ADMIN, now=NOW)

    # PW-A
    def test_pw_a_front_page(self):
        html = WebClient(self.app).get("/")[2]
        self.assertIn("Cómo funciona", html)
        self.assertIn("Pides hasta el miércoles 20:00", html)
        self.assertIn("Compramos juntos al por mayor", html)
        self.assertIn("te devolvemos lo ahorrado", html)
        self.assertIn("Nunca pagas más del precio que ves", html)
        self.assertIn("Entrar para pedir", html)
        self.assertIn('class="logo"', html)

    # PW-B
    def test_pw_b_current_page_in_navigation(self):
        for client, path, label in ((self.web, "/", "Catálogo"), (self.web, "/cuenta", "Mi cuenta"),
                                    (self.admin, "/admin", "Admin")):
            with self.subTest(path=path):
                html = client.get(path)[2]
                self.assertRegex(html, rf'<a href="{path}" aria-current="page">{label}</a>')
                self.assertEqual(html.count('aria-current="page"'), 1)

    # PW-C
    def test_pw_c_progress_bar(self):
        self.web.post("/pedidos", {"cant_PAPA-AMARILLA": "5", "cant_PAPA-BLANCA": "10", "cant_CEBOLLA-ROJA": "10",
                                   "metodo": "YAPE", "codigo": "OP-1", "monto": "61.00", "saldo": "0"})
        html = self.web.get("/")[2]
        self.assertIn('<progress value="5" max="100"', html)
        self.assertIn("5 de 100 kg", html)

    # PW-D
    def test_pw_d_savings_badge(self):
        self.supermarket("7.99")
        self.assertIn("49.5 % menos que en Plaza Vea", WebClient(self.app).get("/")[2])

    def test_pw_d_no_badge_when_reference_is_cheaper(self):
        self.supermarket("3.00")
        html = WebClient(self.app).get("/")[2]
        self.assertNotIn("menos que en", html)
        self.assertIn("Plaza Vea: S/ 3.00", html)

    # PW-E
    def test_pw_e_account_balance_first(self):
        html = self.web.get("/cuenta")[2]
        self.assertIn('class="hero-balance"', html)
        self.assertIn("Saldo: S/ 0.00", html)
        self.assertLess(html.index('class="hero-balance"'), html.index('action="/cuenta/devolucion"'))

    # PW-F
    def test_pw_f_admin_tiles(self):
        html = self.admin.get("/admin")[2]
        tiles = html[html.index('class="tiles"'):]
        for path in ("/admin/armado", "/admin/reclamos", "/admin/colchon", "/admin/metricas", "/admin/devoluciones",
                     "/admin/conciliacion", "/admin/catalogo", "/admin/referencias", "/admin/vecinos"):
            with self.subTest(path=path):
                self.assertRegex(tiles, rf'<a class="tile" href="{path}"><strong>[^<]+</strong><span>[^<]+</span></a>')

    # PW-G
    def test_pw_g_no_external_resources(self):
        pages = [WebClient(self.app).get("/")[2], WebClient(self.app).get("/entrar")[2], self.web.get("/cuenta")[2],
                 self.admin.get("/admin")[2]]
        for html in pages:
            for pattern in ('src="http', 'href="http', "@import", "url("):
                self.assertNotIn(pattern, html)


class DemoWeekSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        from yapa_sdd.demo import demo_store

        self.store = demo_store()

    # PW-H
    def test_pw_h_demo_week(self):
        self.assertEqual(money_balance(self.store).difference, D("0"))
        ana = self.store.find_order(101, "2026-W39")
        self.assertEqual(ana.status, "LIQUIDADO")
        self.assertGreater(self.store.settlements["2026-W39"].orders[ana.order_id].refund_amount, D("0"))
        self.assertGreaterEqual(len(self.store.orders_in_cycle("2026-W40")), 5)
        current = reference.current_references(self.store, "PAPA-AMARILLA", date(2026, 9, 30))
        self.assertIn("SUPERMERCADO", current)
        self.assertFalse([r for r in self.store.reference_prices if r.kind == "MERCADO"])

    # PW-I
    def test_pw_i_demo_through_the_web(self):
        set_pin(self.store, 101, PIN)
        app = create_app(self.store, clock=lambda: DEMO_NOW)
        web = WebClient(app)
        web.login(101, PIN)
        html = web.get("/cuenta")[2]
        self.assertIn("Con Yapa ya te devolvimos", html)
        self.assertIn("En el supermercado costaba", html)
        self.assertRegex(web.get("/")[2], r"[\d.]+ % menos que en Plaza Vea")


if __name__ == "__main__":
    unittest.main()
