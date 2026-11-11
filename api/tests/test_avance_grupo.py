"""Iteración 62: el vecino ve el avance de su grupo en la semana (docs/desarrollo/62-avance-del-grupo-para-el-vecino.md)."""

from datetime import datetime
import unittest

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd.auth import set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer
from yapa_sdd.order_changes import cancel_order
from yapa_sdd.order_registration import register_order, verify_payment
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)  # 2026-W38
LAST_WEEK = datetime(2026, 9, 9, 10, 0, tzinfo=LIMA)  # 2026-W37
BASKET = [("PAPA-AMARILLA", "5"), ("PAPA-BLANCA", "10"), ("CEBOLLA-ROJA", "10")]  # S/ 61.00
PINS = {101: "482915", 105: "739104", 140: "615283"}


class GroupProgressSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        for customer_id, zone_id in ((130, "Z-LINCE-02"), (120, "Z-LINCE-01"), (121, "Z-LINCE-01"),
                                     (801, "Z-JM-01"), (140, "Z-NINGUNA")):
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", zone_id))
        for customer_id, pin in PINS.items():
            set_pin(self.store, customer_id, pin)
        for customer_id in (101, 105, 130):
            self.order(customer_id)
        self.api = create_api(self.store, clock=lambda: NOW)

    def order(self, customer_id, *, verified=True, now=NOW):
        order = register_order(self.store, customer_id=customer_id, lines=BASKET, payment_method="YAPE",
                               operation_code=f"OP-{now:%V}-{customer_id}", amount="61.00", now=now)
        if verified:
            verify_payment(self.store, order.order_id, now=now)
        return order

    def my_zone(self, customer_id):
        client = ApiClient(self.api)
        client.login(customer_id, PINS[customer_id])
        status, body, _ = client.get("/api/mi-zona")
        self.assertEqual(status, 200)
        return body

    # AG-A
    def test_ag_a_neighbor_sees_group_progress(self):
        body = self.my_zone(105)
        self.assertEqual(body["avance"], {"verificados": 3, "minimo": 8, "ciclo": "2026-W38"})
        self.assertIsNone(body["administra"])

    # AG-B
    def test_ag_b_only_verified_orders_of_the_group_this_week(self):
        self.order(120, verified=False)
        cancelled = self.order(121)
        cancel_order(self.store, cancelled.order_id, customer_id=121, now=NOW)
        self.order(801)
        self.order(101, now=LAST_WEEK)
        self.assertEqual(self.my_zone(105)["avance"]["verificados"], 3)

    # AG-C
    def test_ag_c_only_the_count(self):
        self.assertEqual(set(self.my_zone(105)["avance"]), {"verificados", "minimo", "ciclo"})

    # AG-D
    def test_ag_d_no_zone_no_progress(self):
        body = self.my_zone(140)
        self.assertIn("avance", body)
        self.assertIsNone(body["avance"])

    # AG-E
    def test_ag_e_same_number_as_zone_admin(self):
        self.store.zones["Z-LINCE-01"].admin_id = 101
        body = self.my_zone(101)
        self.assertEqual(body["avance"], body["administra"]["avance"])
        self.assertEqual((body["avance"]["verificados"], body["avance"]["minimo"]), (3, 8))

    # AG-F
    def test_ag_f_requires_session(self):
        status, body, _ = ApiClient(self.api).get("/api/mi-zona")
        self.assertEqual((status, body["error"]["codigo"]), (401, "LOGIN_REQUIRED"))


if __name__ == "__main__":
    unittest.main()
