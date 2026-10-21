"""Criterios de la iteración 22 (docs/desarrollo/22-precio-referencia.md)."""

from datetime import date, datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario
from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.reference import current_references, reference_savings, register_reference
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.app import create_app


ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"
THURSDAY = datetime(2026, 9, 17, 18, 0, tzinfo=LIMA)
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
OBSERVED = date(2026, 9, 17)
SUPER, MARKET = "Plaza Vea online", "Mercado de Lince"
PRICES = {  # producto: (supermercado, mercado)
    "PAPA-AMARILLA": ("7.99", "4.50"),
    "PAPA-BLANCA": ("2.39", "1.50"),
    "CEBOLLA-ROJA": ("3.89", "2.50"),
}


class ReferenceBase(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store

    def register(self, product_id, kind, price, source, observed=OBSERVED, by=ADMIN, now=THURSDAY):
        return register_reference(self.store, product_id, kind, D(price), source, observed, by=by, now=now)

    def register_all(self, skip=()):
        for product_id, (super_price, market_price) in PRICES.items():
            self.register(product_id, "SUPERMERCADO", super_price, SUPER)
            if product_id not in skip:
                self.register(product_id, "MERCADO", market_price, MARKET)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)


class ReferenceSpecTests(ReferenceBase):
    # RF-A
    def test_rf_a_register_keeps_source_date_and_author(self):
        reference = self.register("PAPA-AMARILLA", "MERCADO", "4.50", MARKET)
        self.assertEqual((reference.product_id, reference.kind, reference.price, reference.source,
                          reference.observed_on, reference.by),
                         ("PAPA-AMARILLA", "MERCADO", D("4.50"), MARKET, OBSERVED, ADMIN))
        self.assertEqual(len(self.store.reference_prices), 1)

    # RF-B (vigencia)
    def test_rf_b_references_expire_after_14_days(self):
        self.register_all()
        current = current_references(self.store, "PAPA-AMARILLA", date(2026, 9, 18))
        self.assertEqual(current["MERCADO"].price, D("4.50"))
        self.assertEqual(current["SUPERMERCADO"].price, D("7.99"))
        self.assertEqual(set(current_references(self.store, "PAPA-AMARILLA", date(2026, 10, 1))),
                         {"MERCADO", "SUPERMERCADO"})
        self.assertEqual(current_references(self.store, "PAPA-AMARILLA", date(2026, 10, 2)), {})

    # RF-C
    def test_rf_c_invalid_data(self):
        self.assertRule("INVALID_REFERENCE_KIND", self.register, "PAPA-AMARILLA", "FERIA", "4.50", MARKET)
        self.assertRule("INVALID_PRICE", self.register, "PAPA-AMARILLA", "MERCADO", "0", MARKET)
        self.assertRule("SOURCE_REQUIRED", self.register, "PAPA-AMARILLA", "MERCADO", "4.50", "  ")
        self.assertRule("INVALID_DATE", self.register, "PAPA-AMARILLA", "MERCADO", "4.50", MARKET,
                        observed=date(2026, 9, 19), now=FRIDAY)
        self.assertRule("PRODUCT_NOT_AVAILABLE", self.register, "MANDARINA", "MERCADO", "4.50", MARKET)
        self.assertRule("NOT_AUTHORIZED", self.register, "PAPA-AMARILLA", "MERCADO", "4.50", MARKET, by="vecino-1")
        self.assertEqual(self.store.reference_prices, [])

    # RF-D
    def test_rf_d_most_recent_observation_wins(self):
        self.register_all()
        self.register("PAPA-AMARILLA", "MERCADO", "4.80", MARKET, observed=date(2026, 9, 15), now=FRIDAY)
        self.assertEqual(current_references(self.store, "PAPA-AMARILLA", date(2026, 9, 18))["MERCADO"].price,
                         D("4.50"))

    # RF-E
    def test_rf_e_cycle_savings_against_each_reference(self):
        self.s.orders("Z-JM-01", 8)
        self.register_all()
        settle_cycle(self.store, CYCLE)
        savings = reference_savings(self.store, CYCLE)
        supermarket, market = savings["SUPERMERCADO"], savings["MERCADO"]
        self.assertEqual((supermarket.baskets, supermarket.reference_total, supermarket.yapa_total,
                          supermarket.savings), (8, D("822.00"), D("461.12"), D("360.88")))
        self.assertEqual(supermarket.percent.quantize(D("0.1")), D("43.9"))
        self.assertEqual((market.baskets, market.reference_total, market.yapa_total, market.savings),
                         (8, D("500.00"), D("461.12"), D("38.88")))
        self.assertEqual(market.percent.quantize(D("0.1")), D("7.8"))

    # RF-F
    def test_rf_f_incomplete_basket_is_not_comparable(self):
        self.s.orders("Z-JM-01", 8)
        self.register_all(skip={"CEBOLLA-ROJA"})
        settle_cycle(self.store, CYCLE)
        market = reference_savings(self.store, CYCLE)["MERCADO"]
        self.assertEqual((market.baskets, market.savings, market.percent), (0, D("0"), None))
        self.assertEqual(reference_savings(self.store, CYCLE)["SUPERMERCADO"].baskets, 8)

    # RF-I
    def test_rf_i_references_survive_database(self):
        import os
        import tempfile
        from yapa_sdd import persistence
        self.register("PAPA-AMARILLA", "MERCADO", "4.50", MARKET)
        path = os.path.join(tempfile.mkdtemp(), "yapa.db")
        persistence.save(self.store, path)
        self.assertEqual(persistence.load(path).reference_prices, self.store.reference_prices)

    def test_rf08_cycle_must_be_settled(self):
        self.assertRule("CYCLE_NOT_SETTLED", reference_savings, self.store, CYCLE)


class ReferenceWebTests(ReferenceBase):
    def setUp(self):
        super().setUp()
        fast_hashing(self)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.now = THURSDAY
        self.app = create_app(self.store, clock=lambda: self.now)
        self.admin = WebClient(self.app)
        self.admin.login(ADMIN, ADMIN_PASS, kind="admin")

    def post_all(self):
        for product_id, (super_price, market_price) in PRICES.items():
            for kind, price, source in (("SUPERMERCADO", super_price, SUPER), ("MERCADO", market_price, MARKET)):
                status, _, _ = self.admin.post("/admin/referencias", {"producto": product_id, "tipo": kind,
                                                                      "precio": price, "fuente": source,
                                                                      "fecha": "2026-09-17"})
                self.assertEqual(status, 200)

    # RF-A (web)
    def test_rf_a_register_from_web(self):
        self.post_all()
        self.assertEqual(len(self.store.reference_prices), 6)
        status, _, html = self.admin.post("/admin/referencias", {"producto": "PAPA-AMARILLA", "tipo": "MERCADO",
                                                                 "precio": "4.50", "fuente": MARKET,
                                                                 "fecha": "17/09/2026"})
        self.assertEqual(status, 422)
        self.assertIn("INVALID_INPUT", html)

    # RF-B
    def test_rf_b_neighbor_catalog_shows_references(self):
        self.post_all()
        self.now = FRIDAY
        html = WebClient(self.app).get("/")[2]
        self.assertIn(f"{MARKET}: S/ 4.50", html)
        self.assertIn(f"{SUPER}: S/ 7.99", html)
        self.assertIn("17/09", html)
        self.now = datetime(2026, 10, 2, 10, 0, tzinfo=LIMA)
        html = WebClient(self.app).get("/")[2]
        self.assertNotIn(MARKET, html)

    # RF-G
    def test_rf_g_admin_page_marks_low_savings(self):
        self.post_all()
        status, _, html = self.admin.get("/admin/referencias")
        self.assertEqual(status, 200)
        self.assertIn("S/ 4.03", html)
        self.assertIn("10.4 %", html)
        self.assertIn("menos de 15 %", html)
        self.assertIn("49.5 %", html)

    # RF-H
    def test_rf_h_metrics_page_shows_savings(self):
        self.s.orders("Z-JM-01", 8)
        self.post_all()
        settle_cycle(self.store, CYCLE)
        status, _, html = self.admin.get(f"/admin/metricas?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertIn("43.9 %", html)
        self.assertIn("7.8 %", html)

    # RF-C (web)
    def test_rf_c_neighbor_forbidden(self):
        set_pin(self.store, 101, PIN)
        neighbor = WebClient(self.app)
        neighbor.login(101, PIN)
        status, _, _ = neighbor.post("/admin/referencias", {"producto": "PAPA-AMARILLA", "tipo": "MERCADO",
                                                            "precio": "4.50", "fuente": MARKET, "fecha": "2026-09-17"})
        self.assertEqual(status, 403)
        self.assertEqual(self.store.reference_prices, [])


if __name__ == "__main__":
    unittest.main()
