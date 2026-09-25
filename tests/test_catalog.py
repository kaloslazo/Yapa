from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import Scenario

from yapa_sdd.catalog import deactivate_product, publish_catalog
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer, PriceTier, Product
from yapa_sdd.order_registration import quote_order, register_order, verify_payment
from yapa_sdd.settlement import settle_cycle


W39 = "2026-W39"
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
MONDAY = datetime(2026, 9, 21, 10, 0, tzinfo=LIMA)
TUESDAY = datetime(2026, 9, 22, 10, 0, tzinfo=LIMA)
ADMIN = "admin-yapa"


def product(product_id="PAPA-AMARILLA", tiers=(("0", "3.50"), ("100", "3.30")), max_available="300",
            category="FRESCOS", unit="kg", step="1", supplier="SUP-FRESCOS"):
    return Product(product_id, product_id.title(), category, unit, D(step), D(max_available),
                   tuple(PriceTier(D(q), D(p)) for q, p in tiers), supplier_id=supplier)


def w39_catalog():
    return [product(),
            product("LIMPIATODO-GALON", (("0", "7.90"), ("12", "6.90")), "60", "LIMPIEZA", "unidad",
                    supplier="SUP-LIMPIEZA")]


LINES = [("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "4")]


class CatalogSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def publish(self, products=None, by=ADMIN, now=SATURDAY):
        return publish_catalog(self.store, W39, w39_catalog() if products is None else products, by=by, now=now)

    def order_w39(self, customer_id, lines=LINES, zone="Z-JM-01"):
        self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", zone))
        order = register_order(self.store, customer_id=customer_id, lines=lines, payment_method="YAPE",
                               operation_code=f"W39-{customer_id}", amount=quote_order(self.store, lines, W39).total,
                               now=MONDAY)
        verify_payment(self.store, order.order_id, now=MONDAY)
        return order

    # CT-A
    def test_ct_a_orders_use_the_cycle_catalog(self):
        self.publish()
        quote = quote_order(self.store, LINES, W39)
        self.assertEqual(quote.lines[0].max_unit_price, D("3.92"))
        order = self.order_w39(5001)
        self.assertEqual(order.lines[0].max_unit_price, D("3.92"))

    # CT-B
    def test_ct_b_only_admin_publishes(self):
        self.assertRule("NOT_AUTHORIZED", self.publish, by="vecino-101")

    # CT-C
    def test_ct_c_supplier_must_be_allied(self):
        self.assertRule("SUPPLIER_NOT_ALLIED", self.publish, products=[product(supplier="SUP-OTRO")])
        self.assertRule("SUPPLIER_NOT_ALLIED", self.publish, products=[product(supplier="SUP-NO-EXISTE")])

    # CT-D
    def test_ct_d_invalid_tiers(self):
        for tiers in ((("10", "3.50"),), (("0", "3.50"), ("100", "3.60")), (("0", "0"),),
                      (("0", "3.50"), ("0", "3.30"))):
            with self.subTest(tiers=tiers):
                self.assertRule("INVALID_TIERS", self.publish, products=[product(tiers=tiers)])

    # CT-E
    def test_ct_e_invalid_stock(self):
        self.assertRule("INVALID_STOCK", self.publish, products=[product(max_available="0")])
        self.assertRule("INVALID_STOCK", self.publish, products=[product(max_available="10.5")])

    # CT-F
    def test_ct_f_duplicate_product(self):
        self.assertRule("DUPLICATE_PRODUCT", self.publish, products=[product(), product()])

    # CT-G
    def test_ct_g_invalid_category(self):
        self.assertRule("INVALID_CATEGORY", self.publish, products=[product(category="ABARROTES")])

    # CT-H
    def test_ct_h_all_or_nothing(self):
        self.assertRule("INVALID_STOCK", self.publish, products=[product(), product("LIMON", max_available="0")])
        self.assertNotIn(W39, self.store.catalogs)

    # CT-I
    def test_ct_i_catalog_locked_once_cycle_opens(self):
        self.publish()
        self.assertRule("CATALOG_LOCKED", self.publish, now=TUESDAY)
        self.assertRule("CATALOG_LOCKED", self.publish, now=MONDAY)

    # CT-J
    def test_ct_j_deactivate_mid_week(self):
        self.publish()
        first = self.order_w39(5001)
        self.assertRule("NOT_AUTHORIZED", deactivate_product, self.store, W39, "PAPA-AMARILLA", by="vecino-1")
        deactivate_product(self.store, W39, "PAPA-AMARILLA", by=ADMIN)
        self.assertRule("PRODUCT_NOT_AVAILABLE", self.order_w39, 5002)
        self.assertRule("PRODUCT_NOT_AVAILABLE", deactivate_product, self.store, W39, "MANDARINA", by=ADMIN)
        for i in range(7):
            self.order_w39(5100 + i, lines=[("LIMPIATODO-GALON", "6")])
        result = settle_cycle(self.store, W39)
        self.assertEqual(result.orders[first.order_id].status, "LIQUIDADO")

    # CT-K
    def test_ct_k_stock_is_per_cycle(self):
        self.publish()
        self.store.reserve("PAPA-AMARILLA", D("395"), "2026-W38")
        order = self.order_w39(5001, lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "4")])
        self.assertEqual(self.store.reserved_quantity("PAPA-AMARILLA", W39), D("6"))

    # CT-L
    def test_ct_l_settlement_uses_cycle_tiers(self):
        self.publish()
        for i in range(20):  # 200 kg de papa (tramo desde 100) y 40 galones (dentro del máximo de 60)
            self.order_w39(5200 + i, lines=[("PAPA-AMARILLA", "10"), ("LIMPIATODO-GALON", "2")])
        result = settle_cycle(self.store, W39)
        self.assertEqual(result.products["PAPA-AMARILLA"].final_unit_price, D("3.696"))


if __name__ == "__main__":
    unittest.main()
