from datetime import datetime
from decimal import Decimal
import unittest

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, PriceTier, Product
from yapa_sdd.order_registration import quote_order, register_order, verify_payment
from yapa_sdd.seed import pilot_store


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)

CA01_LINES = [
    ("PAPA-AMARILLA", "5"),
    ("CEBOLLA-ROJA", "3"),
    ("LIMON", "2"),
    ("AJO", "1"),
    ("LIMPIATODO-GALON", "2"),
]


def register(store, customer_id=101, lines=None, method="YAPE", code="04512873", amount=None, now=NOW):
    lines = CA01_LINES if lines is None else lines
    if amount is None:
        amount = quote_order(store, lines).total
    return register_order(
        store,
        customer_id=customer_id,
        lines=lines,
        payment_method=method,
        operation_code=code,
        amount=amount,
        now=now,
    )


class RegisterOrderSpecTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()

    def assertRule(self, expected, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            register(self.store, **kwargs)
        self.assertEqual(raised.exception.code, expected)
        return raised.exception

    # CA-01
    def test_ca01_registers_valid_order(self):
        order = register(self.store, amount=Decimal("59.51"))
        self.assertEqual(order.status, "REGISTRADO")
        self.assertEqual(order.payment_status, "POR_VERIFICAR")
        self.assertEqual(order.cycle, "2026-W38")
        self.assertEqual(order.zone_id, "Z-LINCE-01")
        self.assertEqual(order.lines[0].max_unit_price, Decimal("4.032"))
        self.assertEqual(order.subtotal, Decimal("54.518"))
        self.assertEqual(order.delivery_fee, Decimal("5.00"))
        self.assertEqual(order.total, Decimal("59.51"))

    # CA-02
    def test_ca02_rejects_suspended_customer(self):
        self.assertRule("CUSTOMER_SUSPENDED", customer_id=102)

    def test_ca02_rejects_unknown_customer(self):
        self.assertRule("CUSTOMER_NOT_FOUND", customer_id=999)

    # CA-03
    def test_ca03_rejects_zone_outside_pilot(self):
        self.assertRule("ZONE_NOT_AVAILABLE", customer_id=104)

    def test_ca03_rejects_zone_without_accepted_reception(self):
        self.assertRule("ZONE_NOT_AVAILABLE", customer_id=103)

    # CA-04
    def test_ca04_accepts_one_second_before_close(self):
        order = register(self.store, now=datetime(2026, 9, 16, 19, 59, 59, tzinfo=LIMA))
        self.assertEqual(order.status, "REGISTRADO")

    def test_ca04_accepts_monday_midnight(self):
        order = register(self.store, now=datetime(2026, 9, 14, 0, 0, tzinfo=LIMA))
        self.assertEqual(order.cycle, "2026-W38")

    def test_ca04_rejects_exactly_at_close(self):
        self.assertRule("CYCLE_CLOSED", now=datetime(2026, 9, 16, 20, 0, tzinfo=LIMA))

    def test_ca04_rejects_thursday(self):
        self.assertRule("CYCLE_CLOSED", now=datetime(2026, 9, 17, 9, 0, tzinfo=LIMA))

    # CA-05
    def test_ca05_rejects_second_order_in_cycle(self):
        register(self.store, code="1111")
        self.assertRule("ORDER_ALREADY_EXISTS", code="2222")

    # CA-06
    def test_ca06_rejects_empty_order(self):
        self.assertRule("EMPTY_ORDER", lines=[], amount=Decimal("5.00"))

    # CA-07
    def test_ca07_merges_repeated_product_lines(self):
        lines = [("PAPA-AMARILLA", "3"), ("PAPA-AMARILLA", "3"), ("LIMPIATODO-GALON", "4")]
        order = register(self.store, lines=lines)
        self.assertEqual(len(order.lines), 2)
        self.assertEqual(order.lines[0].product_id, "PAPA-AMARILLA")
        self.assertEqual(order.lines[0].quantity, Decimal("6"))

    # CA-08
    def test_ca08_rejects_product_not_in_catalog(self):
        self.assertRule("PRODUCT_NOT_AVAILABLE", lines=CA01_LINES + [("MANDARINA", "2")], amount=Decimal("60"))

    def test_ca08_rejects_inactive_product(self):
        self.assertRule("PRODUCT_NOT_AVAILABLE", lines=CA01_LINES + [("PLATANO-SEDA", "2")], amount=Decimal("60"))

    # CA-09
    def test_ca09_rejects_invalid_quantities(self):
        for bad in (("PAPA-AMARILLA", "0.5"), ("PAPA-AMARILLA", "11"), ("LIMPIATODO-GALON", "1.5"), ("LIMON", "0")):
            with self.subTest(line=bad):
                self.assertRule("INVALID_QUANTITY", lines=[bad, ("DETERGENTE-LIQUIDO-GALON", "4")], amount=Decimal("60"))

    def test_ca09_rejects_non_numeric_quantities(self):
        for bad in ("NaN", "Infinity", "abc"):
            with self.subTest(quantity=bad):
                self.assertRule("INVALID_QUANTITY", lines=[("PAPA-AMARILLA", bad)], amount=Decimal("60"))

    def test_ca09_accepts_garlic_in_quarter_kilos(self):
        lines = [("AJO", "0.25"), ("LIMPIATODO-GALON", "6")]
        order = register(self.store, lines=lines)
        self.assertEqual(order.lines[0].quantity, Decimal("0.25"))

    # CA-10
    def test_ca10_rejects_quantity_above_supplier_stock(self):
        self.store.reserve("PAPA-AMARILLA", Decimal("395"))
        self.assertRule("PRODUCT_SOLD_OUT", lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "4")], amount=Decimal("60"))

    def test_ca10_accepts_exactly_remaining_stock_and_reserves_it(self):
        self.store.reserve("PAPA-AMARILLA", Decimal("395"))
        register(self.store, lines=[("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "4")])
        self.assertEqual(self.store.reserved["PAPA-AMARILLA"], Decimal("400"))

    # CA-11
    def test_ca11_minimum_uses_exact_subtotal(self):
        self.store.add_product(Product("PRUEBA-A", "Prueba", "FRESCOS", "unidad", Decimal("1"), Decimal("10"),
                                       (PriceTier(Decimal("0"), Decimal("44.639")),)))
        error = self.assertRule("SUBTOTAL_BELOW_MINIMUM", lines=[("PRUEBA-A", "1")], amount=Decimal("55"))
        self.assertIn("0.01", str(error))

    def test_ca11_accepts_subtotal_just_above_minimum(self):
        self.store.add_product(Product("PRUEBA-B", "Prueba", "FRESCOS", "unidad", Decimal("1"), Decimal("10"),
                                       (PriceTier(Decimal("0"), Decimal("44.65")),)))
        order = register(self.store, lines=[("PRUEBA-B", "1")])
        self.assertEqual(order.subtotal, Decimal("50.008"))

    # CA-12
    def test_ca12_rejects_payment_method_not_allowed(self):
        self.assertRule("PAYMENT_METHOD_NOT_ALLOWED", method="TARJETA")

    def test_ca12_requires_operation_code(self):
        self.assertRule("PAYMENT_CODE_REQUIRED", code="  ")

    def test_ca12_rejects_reused_operation_code(self):
        register(self.store, customer_id=101, code="555")
        self.assertRule("PAYMENT_CODE_ALREADY_USED", customer_id=105, code="555")

    def test_ca12_rejects_amount_different_from_total(self):
        self.assertRule("PAYMENT_AMOUNT_MISMATCH", amount=Decimal("59.52"))

    def test_ca12_rejects_non_numeric_amount(self):
        self.assertRule("PAYMENT_AMOUNT_MISMATCH", amount="abc")

    def test_plin_is_allowed(self):
        order = register(self.store, method="PLIN")
        self.assertEqual(order.payment_method, "PLIN")

    # CA-13
    def test_ca13_prices_come_from_catalog(self):
        order = register(self.store)
        prices = {line.product_id: line.max_unit_price for line in order.lines}
        self.assertEqual(prices["AJO"], Decimal("5.376"))
        self.assertEqual(prices["LIMPIATODO-GALON"], Decimal("8.611"))

    # CA-15
    def test_ca15_quote_does_not_reserve_or_create_order(self):
        quote = quote_order(self.store, CA01_LINES)
        self.assertEqual(quote.total, Decimal("59.51"))
        self.assertEqual(self.store.orders, {})
        self.assertEqual(self.store.reserved.get("PAPA-AMARILLA", Decimal("0")), Decimal("0"))

    # CA-14
    def test_ca14_admin_verifies_payment_before_close(self):
        order = register(self.store)
        verify_payment(self.store, order.order_id, now=NOW)
        self.assertEqual(self.store.orders[order.order_id].payment_status, "VERIFICADO")

    def test_ca14_rejects_verification_after_close(self):
        order = register(self.store)
        with self.assertRaises(BusinessRuleError) as raised:
            verify_payment(self.store, order.order_id, now=datetime(2026, 9, 16, 20, 0, tzinfo=LIMA))
        self.assertEqual(raised.exception.code, "CYCLE_CLOSED")

    def test_ca14_rejects_unknown_order(self):
        with self.assertRaises(BusinessRuleError) as raised:
            verify_payment(self.store, 999, now=NOW)
        self.assertEqual(raised.exception.code, "ORDER_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
