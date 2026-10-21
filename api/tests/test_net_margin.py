from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import BASKET, CYCLE, Scenario

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.metrics import OPTIMISTIC, PESSIMISTIC, OperatingCosts, net_margins, net_margin_summary
from yapa_sdd.order_registration import register_order, verify_payment
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import credit


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)


class NetMarginSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store

    def settled_mt_a(self):
        orders = self.s.orders("Z-JM-01", 8)
        settle_cycle(self.store, CYCLE)
        return orders

    # NA-01
    def test_na01_optimistic(self):
        orders = self.settled_mt_a()
        margin = net_margins(self.store, CYCLE, OPTIMISTIC)[orders[0].order_id]
        self.assertEqual(margin.operating_cost, D("2.33"))
        self.assertEqual(margin.net_margin, D("3.31"))
        summary = net_margin_summary(self.store, CYCLE, OPTIMISTIC)
        self.assertEqual(summary.orders, 8)
        self.assertEqual(summary.losing_orders, 0)
        self.assertEqual(summary.average_net_margin, D("3.31"))

    # NA-02
    def test_na02_pessimistic(self):
        orders = self.settled_mt_a()
        margin = net_margins(self.store, CYCLE, PESSIMISTIC)[orders[0].order_id]
        self.assertEqual(margin.operating_cost, D("7.4595"))
        self.assertEqual(margin.net_margin, D("-1.8195"))
        summary = net_margin_summary(self.store, CYCLE, PESSIMISTIC)
        self.assertEqual(summary.losing_orders, 8)
        self.assertEqual(summary.shortfall_per_losing_order, D("1.8195"))

    # NA-03
    def test_na03_balance_pays_no_fee(self):
        self.s.orders("Z-JM-01", 7)
        self.store.add_customer(Customer(2001, "Con saldo", "Z-JM-01"))
        credit(self.store, 2001, D("10"), "ABONO_LIQUIDACION", NOW)
        order = register_order(self.store, customer_id=2001, lines=BASKET, payment_method="YAPE",
                               operation_code="NA3", amount=D("51.00"), use_balance=D("10"), now=NOW)
        verify_payment(self.store, order.order_id, now=NOW)
        settle_cycle(self.store, CYCLE)
        margin = net_margins(self.store, CYCLE, PESSIMISTIC)[order.order_id]
        self.assertEqual(margin.payment_fee, D("1.5045"))

    # NA-04
    def test_na04_requires_settled_cycle(self):
        self.s.orders("Z-JM-01", 8)
        with self.assertRaises(BusinessRuleError) as raised:
            net_margin_summary(self.store, CYCLE, OPTIMISTIC)
        self.assertEqual(raised.exception.code, "CYCLE_NOT_SETTLED")

    # NA-05
    def test_na05_custom_scenario(self):
        orders = self.settled_mt_a()
        custom = OperatingCosts("PROPIO", purchase_trip=D("0"), packing=D("1.00"), support=D("0"), payment_fee_rate=D("0"))
        self.assertEqual(net_margins(self.store, CYCLE, custom)[orders[0].order_id].net_margin, D("4.64"))


if __name__ == "__main__":
    unittest.main()
