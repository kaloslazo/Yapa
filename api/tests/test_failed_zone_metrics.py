from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario, buy_all

from yapa_sdd.cycle import LIMA
from yapa_sdd.fulfillment import pack_bag, register_failed_delivery
from yapa_sdd.metrics import delivered_savings, margin_alerts, order_margins
from yapa_sdd.settlement import settle_cycle


SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
STAFF = "admin-yapa"


class FailedZoneMetricsSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.store.admins.add(STAFF)

    def failed_zone(self):
        orders = self.s.orders("Z-JM-01", 8)
        for order in orders:
            pack_bag(self.store, order.order_id, by=STAFF, photo="bolsa.jpg", now=SATURDAY)
        buy_all(self.store, CYCLE)
        register_failed_delivery(self.store, CYCLE, "Z-JM-01", by=STAFF, photo="puerta.jpg",
                                 reason="NADIE_RECIBE", now=SATURDAY)
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        return orders

    # MG-A
    def test_mg_a_loss_is_visible(self):
        orders = self.failed_zone()
        margin = order_margins(self.store, CYCLE)[orders[0].order_id]
        self.assertEqual(margin.revenue, D("5.00"))
        self.assertEqual(margin.product_cost, D("47.00"))
        self.assertEqual(margin.stop_cost, D("5"))
        self.assertEqual(margin.margin, D("-47.00"))
        self.assertEqual(len(margin_alerts(self.store, CYCLE)), 8)

    # MG-B
    def test_mg_b_normal_cycle_unchanged(self):
        orders = self.s.orders("Z-JM-01", 8)
        settle_cycle(self.store, CYCLE)
        self.assertEqual(order_margins(self.store, CYCLE)[orders[0].order_id].margin, D("5.64"))

    # MG-C
    def test_mg_c_savings_unchanged(self):
        self.failed_zone()
        self.assertEqual(delivered_savings(self.store, CYCLE).total, D("0"))


if __name__ == "__main__":
    unittest.main()
