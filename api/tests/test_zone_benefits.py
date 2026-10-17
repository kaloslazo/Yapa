"""Iteración 28: beneficios del admin de zona, referidos y su panel (docs/desarrollo/28-admin-zona-beneficios.md)."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd import customers
from yapa_sdd.audit import money_balance
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.order_registration import register_order, verify_payment
from yapa_sdd.seed import pilot_store
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import balance
from yapa_sdd.web.api import create_api


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
NEXT_WEEK = datetime(2026, 9, 23, 10, 0, tzinfo=LIMA)
BASKET = [("PAPA-AMARILLA", "5"), ("PAPA-BLANCA", "10"), ("CEBOLLA-ROJA", "10")]  # S/ 61.00
JM = list(range(801, 809))
ADMIN = "admin-yapa"


class ZoneBenefitSpecTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()
        for customer_id in JM:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", "Z-JM-01"))

    def order_all(self, now=NOW):
        for customer_id in JM:
            order = register_order(self.store, customer_id=customer_id, lines=BASKET, payment_method="YAPE",
                                   operation_code=f"OP-{now:%V}-{customer_id}", amount="61.00", now=now)
            verify_payment(self.store, order.order_id, now=now)

    def settled(self, customer_id, cycle="2026-W38"):
        order = self.store.find_order(customer_id, cycle)
        return self.store.settlements[cycle].orders[order.order_id]

    # AZ-A
    def test_az_a_free_delivery_for_zone_admin(self):
        self.store.zones["Z-JM-01"].admin_id = 801
        self.order_all()
        settle_cycle(self.store, "2026-W38")
        admin = self.settled(801)
        self.assertEqual((admin.final_amount, admin.refund_amount, admin.benefit), (D("52.64"), D("8.36"), D("5.00")))
        for customer_id in JM[1:]:
            self.assertEqual(self.settled(customer_id).final_amount, D("57.64"))

    # AZ-B
    def test_az_b_temporary_discount(self):
        self.store.zones["Z-JM-01"].admin_id = 801
        self.store.zones["Z-JM-01"].created_cycle = "2026-W37"
        self.order_all()
        settle_cycle(self.store, "2026-W38")
        admin = self.settled(801)
        self.assertEqual((admin.final_amount, admin.refund_amount, admin.benefit), (D("50.00"), D("11.00"), D("7.64")))

    def test_az_b_discount_ends_after_four_weeks(self):
        self.store.zones["Z-JM-01"].admin_id = 801
        self.store.zones["Z-JM-01"].created_cycle = "2026-W34"
        self.order_all()
        settle_cycle(self.store, "2026-W38")
        self.assertEqual(self.settled(801).final_amount, D("52.64"))

    # AZ-C
    def test_az_c_no_admin_no_benefit(self):
        self.order_all()
        settle_cycle(self.store, "2026-W38")
        self.assertEqual({self.settled(c).final_amount for c in JM}, {D("57.64")})
        self.assertEqual({self.settled(c).benefit for c in JM}, {D("0")})

    # AZ-D
    def test_az_d_referral_code(self):
        self.assertEqual(customers.referral_code(self.store.customers[101]), "ANA101")
        self.assertEqual(customers.referral_code(Customer(120, "José Núñez", "Z-JM-01")), "JOSE120")

    # AZ-E
    def test_az_e_register_with_referral(self):
        lucia, _ = customers.register_customer(self.store, "Lucía Ramos", "987654321", "Z-LINCE-01", True, by=ADMIN,
                                               now=NOW, referral="ANA101")
        self.assertEqual(lucia.referred_by, 101)
        before = len(self.store.customers)
        with self.assertRaises(BusinessRuleError) as raised:
            customers.register_customer(self.store, "Otro Vecino", "987654322", "Z-LINCE-01", True, by=ADMIN, now=NOW,
                                        referral="NOEXISTE9")
        self.assertEqual(raised.exception.code, "REFERRAL_NOT_FOUND")
        self.assertEqual(len(self.store.customers), before)

    # AZ-F
    def test_az_f_referral_reward_once(self):
        self.store.add_customer(Customer(808, "Vecino 808", "Z-JM-01", referred_by=801))
        self.order_all()
        settle_cycle(self.store, "2026-W38")
        self.assertEqual(balance(self.store, 801), D("3.36") + D("3.00"))
        self.assertEqual(balance(self.store, 808), D("3.36") + D("3.00"))
        rewards = [m for m in self.store.movements if m.kind == "PREMIO_REFERIDO"]
        self.assertEqual(len(rewards), 2)
        self.order_all(NEXT_WEEK)
        settle_cycle(self.store, "2026-W39")
        self.assertEqual(len([m for m in self.store.movements if m.kind == "PREMIO_REFERIDO"]), 2)

    # AZ-G
    def test_az_g_money_still_balances(self):
        self.store.zones["Z-JM-01"].admin_id = 801
        self.store.add_customer(Customer(808, "Vecino 808", "Z-JM-01", referred_by=801))
        self.order_all()
        settle_cycle(self.store, "2026-W38")
        self.assertEqual(money_balance(self.store).difference, D("0"))


class ZoneAdminPanelSpecTests(unittest.TestCase):
    # AZ-H
    def test_az_h_zone_admin_panel(self):
        fast_hashing(self)
        store = pilot_store()
        store.zones["Z-LINCE-01"].admin_id = 101
        store.add_customer(Customer(130, "Vecino 130", "Z-LINCE-02"))
        for customer_id in (101, 105, 130):
            order = register_order(store, customer_id=customer_id, lines=BASKET, payment_method="YAPE",
                                   operation_code=f"OP-{customer_id}", amount="61.00", now=NOW)
            verify_payment(store, order.order_id, now=NOW)
        set_pin(store, 101, "482915")
        set_pin(store, 105, "739104")
        set_admin_password(store, ADMIN, "yapa-admin-2026")
        api = create_api(store, clock=lambda: NOW)
        ana = ApiClient(api)
        ana.login(101, "482915")
        panel = ana.get("/api/mi-zona")[1]["administra"]
        self.assertEqual((panel["avance"]["verificados"], panel["avance"]["minimo"]), (3, 8))
        ordered = {v["id"]: v["pidio"] for v in panel["vecinos"]}
        self.assertEqual(ordered, {101: True, 102: False, 105: True})
        nearby = {z["id"]: z["distancia_m"] for z in panel["cercanas"]}
        self.assertIn("Z-LINCE-02", nearby)
        self.assertLessEqual(nearby["Z-LINCE-02"], 500)
        self.assertNotIn("Z-JM-01", nearby)
        self.assertTrue(panel["beneficios"]["envio_gratis"])
        self.assertEqual(panel["codigo_referido"], "ANA101")
        carmen = ApiClient(api)
        carmen.login(105, "739104")
        self.assertIsNone(carmen.get("/api/mi-zona")[1]["administra"])


if __name__ == "__main__":
    unittest.main()
