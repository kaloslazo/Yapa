from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario, buy_all

from yapa_sdd.claims import file_claim
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import close_cycle, deliver_zone, pack_bag, register_failed_delivery
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import balance


SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
STAFF = "admin-yapa"


class FailedDeliverySpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.store.admins.add(STAFF)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def packed(self, zone_id, count):
        orders = self.s.orders(zone_id, count)
        for order in orders:
            pack_bag(self.store, order.order_id, by=STAFF, photo=f"bolsa-{order.order_id}.jpg", now=SATURDAY)
        return orders

    def fail(self, zone_id="Z-JM-01", reason="PORTERIA_CERRADA", photo="puerta.jpg", by=STAFF):
        buy_all(self.store, CYCLE)
        return register_failed_delivery(self.store, CYCLE, zone_id, by=by, photo=photo, reason=reason, now=SATURDAY)

    # EF-A
    def test_ef_a_register_failure_once(self):
        self.packed("Z-JM-01", 8)
        failure = self.fail()
        self.assertEqual(failure.reason, "PORTERIA_CERRADA")
        self.assertRule("ZONE_ALREADY_CLOSED", self.fail)
        self.assertRule("ZONE_ALREADY_CLOSED", deliver_zone, self.store, CYCLE, "Z-JM-01", by=STAFF,
                        photo="entrega.jpg", received_by="Sr. Ramos", now=SATURDAY)

    # EF-B
    def test_ef_b_refund_minus_real_delivery(self):
        orders = self.packed("Z-JM-01", 8)
        self.fail()
        result = settle_cycle(self.store, CYCLE, at=SATURDAY)
        first = result.orders[orders[0].order_id]
        self.assertEqual(first.status, "NO_ENTREGADO")
        self.assertEqual(first.final_amount, D("5.00"))
        self.assertEqual(first.refund_amount, D("56.00"))
        self.assertEqual(first.refund_destination, "SALDO")
        self.assertEqual(balance(self.store, orders[0].customer_id), D("56.00"))
        self.assertEqual(result.products["PAPA-AMARILLA"].total_quantity, D("40"))

    # EF-C
    def test_ef_c_required_data(self):
        self.packed("Z-JM-01", 8)
        self.assertRule("INVALID_FAILURE_REASON", self.fail, reason="")
        self.assertRule("INVALID_FAILURE_REASON", self.fail, reason="LLUVIA")
        self.assertRule("PHOTO_REQUIRED", self.fail, photo=" ")
        self.assertRule("NOT_AUTHORIZED", self.fail, by="vecino-1")

    def test_ef_c_orders_must_be_packed(self):
        self.s.orders("Z-JM-01", 8)
        self.assertRule("ORDERS_NOT_PACKED", self.fail)

    # EF-D
    def test_ef_d_no_claims_on_failed_zone(self):
        orders = self.packed("Z-JM-01", 8)
        self.fail()
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        self.assertRule("ORDER_NOT_DELIVERED", file_claim, self.store, orders[0].order_id,
                        customer_id=orders[0].customer_id, product_id="CEBOLLA-ROJA", quantity="1", reason="FALTANTE",
                        photo="x.jpg", now=SATURDAY)

    # EF-E
    def test_ef_e_close_cycle_requires_all_zones(self):
        jm = self.packed("Z-JM-01", 8)
        self.packed("Z-LINCE-01", 8)
        buy_all(self.store, CYCLE)
        deliver_zone(self.store, CYCLE, "Z-JM-01", by=STAFF, photo="entrega.jpg", received_by="Sr. Ramos",
                     now=SATURDAY)
        with self.assertRaises(BusinessRuleError) as raised:
            close_cycle(self.store, CYCLE, at=SATURDAY)
        self.assertEqual(raised.exception.code, "ZONES_PENDING")
        self.assertIn("Z-LINCE-01", str(raised.exception))
        self.assertEqual(balance(self.store, jm[0].customer_id), D("0"))

    # EF-F
    def test_ef_f_close_cycle_settles_when_complete(self):
        self.packed("Z-JM-01", 8)
        self.packed("Z-LINCE-01", 8)
        buy_all(self.store, CYCLE)
        deliver_zone(self.store, CYCLE, "Z-JM-01", by=STAFF, photo="entrega.jpg", received_by="Sr. Ramos",
                     now=SATURDAY)
        self.fail(zone_id="Z-LINCE-01", reason="NADIE_RECIBE")
        result = close_cycle(self.store, CYCLE, at=SATURDAY)
        statuses = {o.status for o in result.orders.values()}
        self.assertEqual(statuses, {"LIQUIDADO", "NO_ENTREGADO"})
        self.assertIs(self.store.settlements[CYCLE], result)


if __name__ == "__main__":
    unittest.main()
