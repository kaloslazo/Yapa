from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import BASKET, CYCLE, Scenario, buy_all

from yapa_sdd.claims import file_claim, review_claim
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer, Zone
from yapa_sdd.fulfillment import deliver_zone, pack_bag
from yapa_sdd.metrics import delivered_savings, margin_alerts, order_margins, repurchase_week4
from yapa_sdd.order_registration import quote_order, register_order, verify_payment
from yapa_sdd.settlement import settle_cycle


ADMIN = "admin-yapa"
W41 = "2026-W41"
W41_NOW = datetime(2026, 10, 7, 10, 0, tzinfo=LIMA)
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
SUNDAY = datetime(2026, 9, 20, 8, 0, tzinfo=LIMA)


class MetricsSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def order_w41(self, customer_id):
        if customer_id not in self.store.customers:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", "Z-JM-01"))
        order = register_order(self.store, customer_id=customer_id, lines=BASKET, payment_method="YAPE",
                               operation_code=f"W41-{customer_id}", amount=quote_order(self.store, BASKET, W41).total,
                               now=W41_NOW)
        verify_payment(self.store, order.order_id, now=W41_NOW)
        return order

    def cohort_w38(self):
        cohort = self.s.orders("Z-JM-01", 8)
        self.s.orders("Z-LINCE-01", 7)  # grupo que no llega al mínimo: no compra
        settle_cycle(self.store, CYCLE)
        return [order.customer_id for order in cohort]

    # MT-A
    def test_mt_a_margin_per_order(self):
        orders = self.s.orders("Z-JM-01", 8)
        settle_cycle(self.store, CYCLE)
        margins = order_margins(self.store, CYCLE)
        first = margins[orders[0].order_id]
        self.assertEqual(first.revenue, D("57.64"))
        self.assertEqual(first.product_cost, D("47.00"))
        self.assertEqual(first.stop_cost, D("5"))
        self.assertEqual(first.margin, D("5.64"))
        self.assertEqual(len(margins), 8)
        self.assertEqual(margin_alerts(self.store, CYCLE), [])

    # MT-B
    def test_mt_b_negative_margin_is_alerted(self):
        self.store.add_zone(Zone("Z-JM-LEJOS", "Edificio lejano", "Jesús María", "G-JM-LEJOS", D("100")))
        orders = self.s.orders("Z-JM-LEJOS", 8)
        settle_cycle(self.store, CYCLE)
        margins = order_margins(self.store, CYCLE)
        self.assertEqual(margins[orders[0].order_id].stop_cost, D("12.5"))
        self.assertEqual(margins[orders[0].order_id].margin, D("-1.86"))
        self.assertEqual(margin_alerts(self.store, CYCLE), [o.order_id for o in orders])

    # MT-C
    def test_mt_c_missing_items_and_approved_claims(self):
        orders = self.s.orders("Z-JM-01", 8)
        for order in orders:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)
        buy_all(self.store, CYCLE)
        deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/entrega.jpg", received_by="Sr. Ramos",
                     now=SATURDAY)
        claimed = orders[1]
        claim = file_claim(self.store, claimed.order_id, customer_id=claimed.customer_id, product_id="CEBOLLA-ROJA",
                           quantity="1", reason="DANADO", photo="fotos/cebolla.jpg", now=SUNDAY)
        settle_cycle(self.store, CYCLE, [(orders[0].order_id, "CEBOLLA-ROJA", "2")])
        review_claim(self.store, claim.claim_id, by=ADMIN, approve=True, now=SUNDAY)
        margins = order_margins(self.store, CYCLE)
        missing = margins[orders[0].order_id]
        self.assertEqual(missing.revenue, D("53.60"))
        self.assertEqual(missing.product_cost, D("43.40"))
        self.assertEqual(missing.margin, D("5.20"))
        self.assertEqual(margins[claimed.order_id].claims, D("2.02"))
        self.assertEqual(margins[claimed.order_id].margin, D("3.62"))

    # MT-D
    def test_mt_d_savings_with_8_orders(self):
        self.s.orders("Z-JM-01", 8)
        settle_cycle(self.store, CYCLE)
        savings = delivered_savings(self.store, CYCLE)
        self.assertEqual(savings.volume, D("26.88"))
        self.assertEqual(savings.delivery, D("0"))
        self.assertEqual(savings.total, D("26.88"))

    # MT-E
    def test_mt_e_savings_with_20_orders(self):
        self.s.orders("Z-JM-01", 20)
        settle_cycle(self.store, CYCLE)
        savings = delivered_savings(self.store, CYCLE)
        self.assertEqual(savings.volume, D("197.12"))
        self.assertEqual(savings.delivery, D("60.00"))
        self.assertEqual(savings.total, D("257.12"))

    # MT-F
    def test_mt_f_repurchase_meets_target(self):
        cohort = self.cohort_w38()
        for customer_id in cohort[:5] + [9001, 9002, 9003]:
            self.order_w41(customer_id)
        settle_cycle(self.store, W41)
        result = repurchase_week4(self.store, CYCLE)
        self.assertEqual(result.target_cycle, W41)
        self.assertEqual(result.cohort_size, 8)
        self.assertEqual(result.returned, 5)
        self.assertEqual(result.rate, D("62.5"))
        self.assertTrue(result.meets_target)

    # MT-G
    def test_mt_g_repurchase_below_target(self):
        cohort = self.cohort_w38()
        for customer_id in cohort[:3] + [9001, 9002, 9003, 9004, 9005]:
            self.order_w41(customer_id)
        settle_cycle(self.store, W41)
        result = repurchase_week4(self.store, CYCLE)
        self.assertEqual(result.cohort_size, 8)
        self.assertEqual(result.rate, D("37.5"))
        self.assertFalse(result.meets_target)

    # MT-H
    def test_mt_h_needs_settled_cycles_and_cohort(self):
        self.s.orders("Z-JM-01", 8)
        self.assertRule("CYCLE_NOT_SETTLED", order_margins, self.store, CYCLE)
        self.assertRule("CYCLE_NOT_SETTLED", margin_alerts, self.store, CYCLE)
        self.assertRule("CYCLE_NOT_SETTLED", delivered_savings, self.store, CYCLE)
        self.assertRule("CYCLE_NOT_SETTLED", repurchase_week4, self.store, CYCLE)
        settle_cycle(self.store, CYCLE)
        self.assertRule("CYCLE_NOT_SETTLED", repurchase_week4, self.store, CYCLE)
        settle_cycle(self.store, "2026-W37")
        settle_cycle(self.store, "2026-W40")
        self.assertRule("EMPTY_COHORT", repurchase_week4, self.store, "2026-W37")


if __name__ == "__main__":
    unittest.main()
