"""Criterios de la iteración 21 (docs/desarrollo/21-huecos-armado-colchon.md)."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal as D
import unittest

from test_catalog import MONDAY, SATURDAY as CATALOG_SATURDAY, W39, product, w39_catalog
from test_fulfillment import ADMIN, FRIDAY, FulfillmentBase
from test_settlement import CYCLE
from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_admin_password
from yapa_sdd.buffer import add_to_buffer, use_buffer
from yapa_sdd.catalog import publish_catalog
from yapa_sdd.cycle import LIMA
from yapa_sdd.fulfillment import register_failed_delivery
from yapa_sdd.order_registration import quote_order, register_order
from yapa_sdd.web.app import create_app


LIMPIATODO = [("LIMPIATODO-GALON", "4"), ("PAPA-AMARILLA", "5")]  # S/ 54.60
ADMIN_PASS = "yapa-admin-2026"


class GapsBase(FulfillmentBase):
    def setUp(self):
        super().setUp()
        self.cleaning = self.s.order("Z-JM-01", lines=LIMPIATODO)  # pedido 9
        add_to_buffer(self.store, CYCLE, "LIMPIATODO-GALON", "6", by=ADMIN)

    def use(self, quantity, order_id=None):
        order_id = self.cleaning.order_id if order_id is None else order_id
        return use_buffer(self.store, "LIMPIATODO-GALON", quantity, order_id=order_id, by=ADMIN, now=FRIDAY)


class PackingAfterCloseTests(GapsBase):
    # HC-A
    def test_hc_a_no_bags_after_delivery(self):
        self.pack(self.cleaning)
        self.pack_and_deliver()
        self.assertRule("ZONE_ALREADY_CLOSED", self.pack, self.first)

    def test_hc_a_no_bags_after_failed_delivery(self):
        for order in self.orders + [self.cleaning]:
            self.pack(order)
        register_failed_delivery(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/porteria.jpg",
                                 reason="PORTERIA_CERRADA", now=FRIDAY)
        self.assertRule("ZONE_ALREADY_CLOSED", self.pack, self.first)


class BufferPerOrderTests(GapsBase):
    # HC-B
    def test_hc_b_use_is_recorded_with_order(self):
        stock = self.use("2")
        self.assertEqual((stock.quantity, stock.value), (D("4"), D("31.60")))
        self.assertEqual(len(self.store.buffer_uses), 1)
        record = self.store.buffer_uses[0]
        self.assertEqual((record.order_id, record.product_id, record.quantity, record.value, record.by, record.at),
                         (self.cleaning.order_id, "LIMPIATODO-GALON", D("2"), D("15.80"), ADMIN, FRIDAY))

    # HC-C
    def test_hc_c_cannot_replace_more_than_ordered(self):
        self.use("2")
        self.assertRule("BUFFER_NOT_FOR_ORDER", self.use, "3")
        self.assertEqual(self.store.buffer["LIMPIATODO-GALON"].quantity, D("4"))
        self.use("2")
        self.assertEqual(self.store.buffer["LIMPIATODO-GALON"].quantity, D("2"))

    # HC-D
    def test_hc_d_order_without_that_product(self):
        self.assertRule("BUFFER_NOT_FOR_ORDER", self.use, "1", self.first.order_id)
        self.assertEqual(self.store.buffer_uses, [])

    # HC-E
    def test_hc_e_unknown_or_not_attended_order(self):
        self.assertRule("ORDER_NOT_FOUND", self.use, "1", 999)
        lince = self.s.order("Z-LINCE-01", lines=LIMPIATODO)
        self.assertRule("ORDER_NOT_ATTENDED", self.use, "1", lince.order_id)
        self.assertEqual(self.store.buffer["LIMPIATODO-GALON"].quantity, D("6"))


class BufferWebTests(GapsBase):
    # HC-F
    def test_hc_f_web_asks_for_order_and_lists_uses(self):
        fast_hashing(self)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        admin = WebClient(create_app(self.store, clock=lambda: FRIDAY))
        admin.login(ADMIN, ADMIN_PASS, kind="admin")
        self.assertIn('name="pedido"', admin.get("/admin/colchon")[2])
        status, _, _ = admin.post("/admin/colchon/usar", {"producto": "LIMPIATODO-GALON", "cantidad": "2",
                                                          "pedido": str(self.cleaning.order_id)})
        self.assertEqual(status, 200)
        self.assertIn(f"Pedido {self.cleaning.order_id}", admin.get("/admin/colchon")[2])
        status, _, html = admin.post("/admin/colchon/usar", {"producto": "LIMPIATODO-GALON", "cantidad": "1",
                                                             "pedido": "abc"})
        self.assertEqual(status, 422)
        self.assertIn("INVALID_INPUT", html)


class CatalogGapTests(unittest.TestCase):
    def setUp(self):
        from test_settlement import Scenario
        self.store = Scenario().store

    def publish(self, products, cycle=W39, now=CATALOG_SATURDAY):
        return publish_catalog(self.store, cycle, products, by=ADMIN, now=now)

    def assertRule(self, expected, fn, *args, **kwargs):
        from yapa_sdd.domain import BusinessRuleError
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    # HC-G
    def test_hc_g_unit_must_be_kg_or_whole_units(self):
        self.assertRule("INVALID_UNIT", self.publish, [product(unit="caja")])
        self.assertRule("INVALID_UNIT", self.publish,
                        [product("LEJIA-GALON", (("0", "6.50"),), "60", "LIMPIEZA", "unidad", "0.5", "SUP-LIMPIEZA")])
        self.assertNotIn(W39, self.store.catalogs)
        catalog = self.publish([product("AJO", (("0", "4.80"),), "40", step="0.25")])
        self.assertIn("AJO", catalog)

    # HC-H
    def test_hc_h_supplier_leaving_does_not_change_published_catalog(self):
        self.publish(w39_catalog())
        suppliers = self.store.suppliers
        suppliers["SUP-FRESCOS"] = replace(suppliers["SUP-FRESCOS"], allied=False)  # deja de ser aliado el lunes
        self.assertIn("PAPA-AMARILLA", self.store.catalogs[W39])
        lines = [("PAPA-AMARILLA", "10"), ("LIMPIATODO-GALON", "2")]  # S/ 61.42
        order = register_order(self.store, customer_id=101, lines=lines, payment_method="YAPE",
                               operation_code="HC-H", amount=quote_order(self.store, lines, cycle=W39).total,
                               now=MONDAY)
        self.assertEqual(order.cycle, W39)
        self.assertRule("SUPPLIER_NOT_ALLIED", self.publish, w39_catalog(), "2026-W40",
                        datetime(2026, 9, 26, 10, 0, tzinfo=LIMA))


if __name__ == "__main__":
    unittest.main()
