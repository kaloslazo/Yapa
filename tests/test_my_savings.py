"""Criterios de la iteración 23 (docs/desarrollo/23-mi-ahorro.md)."""

from decimal import Decimal as D

from test_reference import FRIDAY, PIN, ReferenceBase
from test_settlement import CYCLE
from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_pin
from yapa_sdd.reference import order_comparison, reference_savings
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.app import create_app


class MySavingsTests(ReferenceBase):
    def setUp(self):
        super().setUp()
        self.orders = self.s.orders("Z-JM-01", 8)
        self.first = self.orders[0]

    def settle(self):
        settle_cycle(self.store, CYCLE)

    def account(self, order):
        fast_hashing(self)
        set_pin(self.store, order.customer_id, PIN)
        client = WebClient(create_app(self.store, clock=lambda: FRIDAY))
        client.login(order.customer_id, PIN)
        status, _, html = client.get("/cuenta")
        self.assertEqual(status, 200)
        return html

    # MA-A
    def test_ma_a_order_comparison(self):
        self.register_all()
        self.settle()
        comparison = order_comparison(self.store, self.first.order_id)
        self.assertEqual((comparison["MERCADO"].reference_total, comparison["MERCADO"].savings),
                         (D("62.50"), D("4.86")))
        self.assertEqual((comparison["SUPERMERCADO"].reference_total, comparison["SUPERMERCADO"].savings),
                         (D("102.75"), D("45.11")))

    # MA-B
    def test_ma_b_no_comparison_without_prices_or_settlement(self):
        self.register_all()
        self.assertEqual(order_comparison(self.store, self.first.order_id), {})
        self.store.reference_prices.clear()
        self.settle()
        self.assertEqual(order_comparison(self.store, self.first.order_id), {})

    # MA-C
    def test_ma_c_account_shows_refund_and_savings(self):
        self.register_all()
        self.settle()
        html = self.account(self.first)
        self.assertIn("Pagaste S/ 61.00", html)
        self.assertIn("costó S/ 57.64", html)
        self.assertIn("te devolvimos S/ 3.36 a tu saldo", html)
        self.assertIn("En el mercado de barrio costaba S/ 62.50: ahorraste S/ 4.86", html)
        self.assertIn("Con Yapa ya te devolvimos S/ 3.36", html)

    # MA-D
    def test_ma_d_says_when_market_was_cheaper(self):
        self.register_all()
        self.register("PAPA-BLANCA", "MERCADO", "1.00", "Mercado de Lince")
        self.settle()
        self.assertEqual(order_comparison(self.store, self.first.order_id)["MERCADO"].savings, D("-0.14"))
        html = self.account(self.first)
        self.assertIn("En el mercado de barrio costaba S/ 57.50: pagaste S/ 0.14 más", html)

    # MA-E
    def test_ma_e_not_attended_order(self):
        lince = self.s.order("Z-LINCE-01")
        self.settle()
        html = self.account(lince)
        self.assertIn("no se atendió", html)
        self.assertIn("te devolvimos S/ 61.00", html)
        self.assertIn("Con Yapa ya te devolvimos S/ 61.00", html)

    # MA-F
    def test_ma_f_cycle_numbers_do_not_change(self):
        self.register_all()
        self.settle()
        savings = reference_savings(self.store, CYCLE)
        self.assertEqual(savings["SUPERMERCADO"].percent.quantize(D("0.1")), D("43.9"))
        self.assertEqual(savings["MERCADO"].percent.quantize(D("0.1")), D("7.8"))
        self.assertEqual(savings["MERCADO"].savings, D("38.88"))


if __name__ == "__main__":
    import unittest
    unittest.main()
