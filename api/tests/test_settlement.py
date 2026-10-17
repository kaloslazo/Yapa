from datetime import datetime
from decimal import Decimal
import unittest

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.order_registration import quote_order, register_order, verify_payment
from yapa_sdd.seed import pilot_store
from yapa_sdd.settlement import settle_cycle


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
CYCLE = "2026-W38"

# 5 kg papa amarilla + 10 kg papa blanca + 10 kg cebolla = S/ 56.00 + S/ 5.00 de envío
BASKET = [("PAPA-AMARILLA", "5"), ("PAPA-BLANCA", "10"), ("CEBOLLA-ROJA", "10")]


class Scenario:
    def __init__(self):
        self.store = pilot_store()
        self.next_customer = 1000

    def order(self, zone_id, lines=BASKET, verified=True):
        self.next_customer += 1
        customer_id = self.next_customer
        self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", zone_id))
        order = register_order(
            self.store,
            customer_id=customer_id,
            lines=lines,
            payment_method="YAPE",
            operation_code=f"OP{customer_id}",
            amount=quote_order(self.store, lines).total,
            now=NOW,
        )
        if verified:
            verify_payment(self.store, order.order_id, now=NOW)
        return order

    def orders(self, zone_id, count, **kwargs):
        return [self.order(zone_id, **kwargs) for _ in range(count)]


class SettleCycleSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()

    # CL-01
    def test_cl01_unverified_order_is_cancelled_and_ignored(self):
        self.s.orders("Z-JM-01", 8)
        pending = self.s.order("Z-JM-01", verified=False)
        result = settle_cycle(self.s.store, CYCLE)
        self.assertEqual(result.orders[pending.order_id].status, "CANCELADO")
        self.assertEqual(result.orders[pending.order_id].refund_amount, Decimal("0"))
        self.assertEqual(result.products["PAPA-AMARILLA"].total_quantity, Decimal("40"))

    # CL-02
    def test_cl02_group_below_minimum_gets_full_refund(self):
        orders = self.s.orders("Z-JM-01", 7)
        result = settle_cycle(self.s.store, CYCLE)
        for order in orders:
            settled = result.orders[order.order_id]
            self.assertEqual(settled.status, "NO_ATENDIDO")
            self.assertEqual(settled.refund_amount, Decimal("61.00"))
            self.assertEqual(settled.refund_destination, "MEDIO_DE_PAGO")

    # CL-03
    def test_cl03_joined_zones_count_together(self):
        orders = self.s.orders("Z-LINCE-01", 4) + self.s.orders("Z-LINCE-02", 4)
        result = settle_cycle(self.s.store, CYCLE)
        for order in orders:
            self.assertEqual(result.orders[order.order_id].status, "LIQUIDADO")

    # CL-04
    def test_cl04_volume_tier_lowers_final_price(self):
        orders = self.s.orders("Z-JM-01", 20)
        result = settle_cycle(self.s.store, CYCLE)
        papa = result.products["PAPA-AMARILLA"]
        self.assertEqual(papa.total_quantity, Decimal("100"))
        self.assertEqual(papa.final_unit_price, Decimal("3.7856"))
        settled = result.orders[orders[0].order_id]
        # 5 x 3.7856 + 10 x 1.0976 + 10 x 1.624 + envio 40/20 = 48.144 -> 48.14
        self.assertEqual(settled.final_amount, Decimal("48.14"))
        self.assertEqual(settled.refund_amount, Decimal("12.86"))
        self.assertEqual(settled.refund_destination, "SALDO")

    # CL-05
    def test_cl05_dropouts_only_reduce_savings(self):
        self.s.orders("Z-JM-01", 19)
        self.s.order("Z-JM-01", verified=False)
        result = settle_cycle(self.s.store, CYCLE)
        papa = result.products["PAPA-AMARILLA"]
        self.assertEqual(papa.total_quantity, Decimal("95"))
        self.assertEqual(papa.final_unit_price, Decimal("4.032"))
        for settled in result.orders.values():
            self.assertGreaterEqual(settled.refund_amount, Decimal("0"))

    # CL-06
    def test_cl06_delivery_is_shared_in_zone(self):
        orders = self.s.orders("Z-JM-01", 10)
        result = settle_cycle(self.s.store, CYCLE)
        self.assertEqual(result.orders[orders[0].order_id].delivery_fee, Decimal("4.00"))

    def test_cl06_delivery_never_exceeds_cap(self):
        small = self.s.orders("Z-LINCE-01", 4)
        self.s.orders("Z-LINCE-02", 4)
        result = settle_cycle(self.s.store, CYCLE)
        self.assertEqual(result.orders[small[0].order_id].delivery_fee, Decimal("5.00"))

    # CL-07
    def test_cl07_missing_item_is_not_charged(self):
        lines = BASKET + [("LIMON", "2")]
        self.s.orders("Z-JM-01", 7)
        target = self.s.order("Z-JM-01", lines=lines)
        base = settle_cycle(pilot_copy(self.s), CYCLE).orders[target.order_id]
        result = settle_cycle(self.s.store, CYCLE, missing=[(target.order_id, "LIMON", "1")])
        settled = result.orders[target.order_id]
        limon = [line for line in settled.lines if line.product_id == "LIMON"][0]
        self.assertEqual(limon.delivered, Decimal("1"))
        self.assertEqual(settled.refund_amount - base.refund_amount, Decimal("2.35"))

    def test_cl07_rejects_missing_greater_than_ordered(self):
        target = self.s.orders("Z-JM-01", 8)[0]
        with self.assertRaises(BusinessRuleError) as raised:
            settle_cycle(self.s.store, CYCLE, missing=[(target.order_id, "PAPA-AMARILLA", "6")])
        self.assertEqual(raised.exception.code, "INVALID_MISSING_ITEM")

    def test_cl07_rejects_missing_product_not_in_order(self):
        target = self.s.orders("Z-JM-01", 8)[0]
        with self.assertRaises(BusinessRuleError) as raised:
            settle_cycle(self.s.store, CYCLE, missing=[(target.order_id, "AJO", "1")])
        self.assertEqual(raised.exception.code, "INVALID_MISSING_ITEM")

    def test_cl07_rejects_missing_for_order_not_delivered(self):
        self.s.orders("Z-JM-01", 8)
        pending = self.s.order("Z-JM-01", verified=False)
        with self.assertRaises(BusinessRuleError) as raised:
            settle_cycle(self.s.store, CYCLE, missing=[(pending.order_id, "CEBOLLA-ROJA", "1")])
        self.assertEqual(raised.exception.code, "INVALID_MISSING_ITEM")

    # CL-08
    def test_cl08_nobody_pays_more_than_shown(self):
        self.s.orders("Z-JM-01", 12)
        self.s.orders("Z-LINCE-01", 5)
        self.s.orders("Z-LINCE-02", 3)
        self.s.order("Z-LINCE-01", verified=False)
        result = settle_cycle(self.s.store, CYCLE, missing=[(1, "CEBOLLA-ROJA", "2")])
        for settled in result.orders.values():
            if settled.status == "LIQUIDADO":
                self.assertGreaterEqual(settled.refund_amount, Decimal("0"))
                self.assertEqual(settled.final_amount + settled.refund_amount, settled.paid)

    # CL-09
    def test_cl09_summary_is_transparent(self):
        self.s.orders("Z-JM-01", 20)
        self.s.orders("Z-LINCE-01", 3)
        result = settle_cycle(self.s.store, CYCLE)
        cebolla = result.products["CEBOLLA-ROJA"]
        self.assertEqual(cebolla.total_quantity, Decimal("200"))
        self.assertEqual(cebolla.tier_min_quantity, Decimal("200"))
        self.assertEqual(cebolla.final_unit_price, Decimal("1.624"))
        self.assertEqual(result.total_refunded, Decimal("183.00"))
        self.assertEqual(result.total_credited, sum(
            (o.refund_amount for o in result.orders.values() if o.status == "LIQUIDADO"), Decimal("0")))


def pilot_copy(scenario):
    """Mismo escenario en un store nuevo, para comparar con y sin faltantes."""
    copy = Scenario()
    for order in scenario.store.orders.values():
        zone_id = scenario.store.customers[order.customer_id].zone_id
        lines = [(line.product_id, line.quantity) for line in order.lines]
        copy.order(zone_id, lines=lines, verified=order.payment_status == "VERIFICADO")
    return copy.store


if __name__ == "__main__":
    unittest.main()
