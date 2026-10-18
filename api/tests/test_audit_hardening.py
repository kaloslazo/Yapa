"""Iteración 30: huecos de la auditoría en el motor (docs/desarrollo/30-auditoria-endurecimiento.md)."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from yapa_sdd.audit import money_balance
from yapa_sdd.buffer import add_to_buffer
from yapa_sdd.claims import _claim_quantity
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.order_changes import cancel_order
from yapa_sdd.order_registration import quote_order, register_order, verify_payment
from yapa_sdd.seed import pilot_store
from yapa_sdd.zones import create_zone, join_zone


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
BASKET = [("PAPA-AMARILLA", "5"), ("PAPA-BLANCA", "10"), ("CEBOLLA-ROJA", "10")]  # S/ 61.00


class AuditHardeningTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def order(self, lines=BASKET, customer_id=101):
        total = quote_order(self.store, lines).total
        return register_order(self.store, customer_id=customer_id, lines=lines, payment_method="YAPE",
                              operation_code=f"OP-{customer_id}", amount=total, now=WEDNESDAY)

    # AD-A
    def test_ad_a_verificar_un_pedido_cancelado_no_entra_a_la_caja(self):
        order = self.order()
        cancel_order(self.store, order.order_id, customer_id=101, now=WEDNESDAY)
        self.assertRule("ORDER_CANCELLED", verify_payment, self.store, order.order_id, now=WEDNESDAY)
        self.assertEqual(self.store.cash_in, [])
        self.assertEqual(money_balance(self.store).difference, D("0"))

    # AD-B
    def test_ad_b_coordenadas_en_texto_se_guardan_como_numeros(self):
        zone = create_zone(self.store, 103, name="Nueva", district="La Victoria", lat="-12.0690", lon="-77.0230",
                           now=WEDNESDAY)
        self.assertEqual((zone.lat, zone.lon), (-12.0690, -77.0230))
        self.store.add_customer(Customer(901, "Vecino", "Z-LV-01", lat=-12.0692, lon=-77.0231))
        join_zone(self.store, 901, zone.zone_id, now=WEDNESDAY)
        self.assertEqual(self.store.customers[901].zone_id, zone.zone_id)

    def test_ad_b_la_zona_exige_nombre(self):
        self.assertRule("NAME_REQUIRED", create_zone, self.store, 103, name="  ", district="La Victoria",
                        lat=-12.0690, lon=-77.0230, now=WEDNESDAY)

    # AD-C
    def test_ad_c_cantidad_enorme_en_el_pedido(self):
        self.assertRule("INVALID_QUANTITY", quote_order, self.store, [("LIMON", "1e999")])

    def test_ad_c_cantidad_enorme_en_un_reclamo(self):
        order = self.order([("LIMON", "10"), ("PAPA-AMARILLA", "7")])
        self.assertRule("INVALID_CLAIM_ITEM", _claim_quantity, self.store, order, "LIMON", "1e999")

    def test_ad_c_cantidad_enorme_en_el_colchon(self):
        self.assertRule("INVALID_QUANTITY", add_to_buffer, self.store, "2026-W38", "LEJIA-GALON", "1e999",
                        by="admin-yapa")


if __name__ == "__main__":
    unittest.main()
