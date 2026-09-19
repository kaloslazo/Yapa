from datetime import datetime
from decimal import Decimal
import unittest

from yapa_sdd.order_registration import (
    CatalogItem,
    CustomerAddress,
    DeliveryWindow,
    OrderLine,
    OrderRegistrationError,
    register_weekly_order,
)


NOW = datetime(2026, 9, 16, 10, 0)
CYCLE_START = datetime(2026, 9, 14, 0, 0)
CYCLE_CLOSE = datetime(2026, 9, 16, 20, 0)


def item(*, price: str = "30.00", active: bool = True, unit: str = "kg", expired: bool = False) -> CatalogItem:
    return CatalogItem(
        product_id=10,
        name="Arroz",
        unit=unit,
        unit_price=Decimal(price),
        active=active,
        valid_from=datetime(2026, 9, 1),
        valid_until=datetime(2026, 9, 15) if expired else datetime(2026, 9, 30),
    )


def valid_order(**overrides):
    values = {
        "order_id": 1200,
        "address": CustomerAddress("Lince", True),
        "lines": [OrderLine(item(), Decimal("2"))],
        "delivery_window": DeliveryWindow("SAT_09_12", 30, 5),
        "payment_method": "TRANSFERENCIA",
        "now": NOW,
        "cycle_start": CYCLE_START,
        "cycle_close": CYCLE_CLOSE,
    }
    values.update(overrides)
    return register_weekly_order(**values)


class RegisterWeeklyOrderSpecTests(unittest.TestCase):
    def test_registers_valid_order(self):
        order = valid_order()
        self.assertEqual(order.status, "REGISTRADO")
        self.assertEqual(order.subtotal, Decimal("60.00"))
        self.assertEqual(order.delivery_fee, Decimal("7.90"))
        self.assertEqual(order.total, Decimal("67.90"))

    def test_rejects_address_outside_pilot(self):
        with self.assertRaisesRegex(OrderRegistrationError, "cobertura") as raised:
            valid_order(address=CustomerAddress("Miraflores", True))
        self.assertEqual(raised.exception.code, "ADDRESS_OUTSIDE_COVERAGE")

    def test_rejects_closed_cycle(self):
        with self.assertRaisesRegex(OrderRegistrationError, "ciclo"):
            valid_order(now=datetime(2026, 9, 17, 9, 0))

    def test_rejects_subtotal_below_minimum(self):
        with self.assertRaisesRegex(OrderRegistrationError, "mínimo"):
            valid_order(lines=[OrderLine(item(price="20.00"), Decimal("2"))])

    def test_delivery_fee_is_waived_from_120(self):
        order = valid_order(lines=[OrderLine(item(price="60.00"), Decimal("2"))])
        self.assertEqual(order.subtotal, Decimal("120.00"))
        self.assertEqual(order.delivery_fee, Decimal("0.00"))

    def test_rejects_expired_price(self):
        with self.assertRaisesRegex(OrderRegistrationError, "vigente"):
            valid_order(lines=[OrderLine(item(expired=True), Decimal("2"))])

    def test_rejects_full_delivery_window(self):
        with self.assertRaisesRegex(OrderRegistrationError, "capacidad"):
            valid_order(delivery_window=DeliveryWindow("SAT_09_12", 30, 30))

    def test_rejects_unknown_payment_method(self):
        with self.assertRaisesRegex(OrderRegistrationError, "habilitado"):
            valid_order(payment_method="TARJETA")


if __name__ == "__main__":
    unittest.main()

