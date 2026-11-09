from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, NOW, Scenario, buy_all

from yapa_sdd import wallet
from yapa_sdd.buffer import add_to_buffer, buffer_value, use_buffer
from yapa_sdd.claims import file_claim, review_claim
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import deliver_zone, pack_bag
from yapa_sdd.order_changes import cancel_order
from yapa_sdd.settlement import settle_cycle


ADMIN = "admin-yapa"
BEFORE_CLOSE = datetime(2026, 9, 16, 19, 59, tzinfo=LIMA)
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
SUNDAY_IN_TIME = datetime(2026, 9, 20, 8, 59, tzinfo=LIMA)
SUNDAY_LATE = datetime(2026, 9, 20, 9, 0, tzinfo=LIMA)


class FulfillmentBase(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)
        self.first = self.orders[0]

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def pack(self, order, photo="fotos/bolsa.jpg", by=ADMIN, now=FRIDAY):
        return pack_bag(self.store, order.order_id, by=by, photo=photo, now=now)

    def deliver(self, zone_id="Z-JM-01", photo="fotos/entrega.jpg", received_by="Sr. Ramos", by=ADMIN):
        buy_all(self.store, CYCLE)
        return deliver_zone(self.store, CYCLE, zone_id, by=by, photo=photo, received_by=received_by, now=SATURDAY)

    def pack_and_deliver(self):
        for order in self.orders:
            self.pack(order)
        return self.deliver()

    def claim(self, quantity="1", product_id="CEBOLLA-ROJA", reason="DANADO", photo="fotos/cebolla.jpg",
              now=SUNDAY_IN_TIME, customer_id=None, order=None):
        order = order or self.first
        return file_claim(self.store, order.order_id, customer_id=customer_id or order.customer_id,
                          product_id=product_id, quantity=quantity, reason=reason, photo=photo, now=now)


class PackingSpecTests(FulfillmentBase):
    # AR-A
    def test_ar_a_bags_are_numbered_with_their_photo(self):
        self.pack(self.first, "fotos/p1-b1.jpg")
        bag = self.pack(self.first, "fotos/p1-b2.jpg")
        self.assertEqual(bag.number, 2)
        self.assertEqual([b.photo for b in self.store.bags[self.first.order_id]], ["fotos/p1-b1.jpg", "fotos/p1-b2.jpg"])

    # AR-B
    def test_ar_b_bag_requires_photo(self):
        self.assertRule("PHOTO_REQUIRED", self.pack, self.first, photo="")
        self.assertRule("PHOTO_REQUIRED", self.pack, self.first, photo="   ")

    # AR-C
    def test_ar_c_cannot_pack_before_close(self):
        self.assertRule("CYCLE_STILL_OPEN", self.pack, self.first, now=BEFORE_CLOSE)

    # AR-D
    def test_ar_d_only_attended_orders_are_packed(self):
        unverified = self.s.order("Z-JM-01", verified=False)
        cancelled = self.s.order("Z-JM-01")
        cancel_order(self.store, cancelled.order_id, customer_id=cancelled.customer_id, now=NOW)
        small_group = self.s.orders("Z-LINCE-01", 7)[0]
        for order in (unverified, cancelled, small_group):
            with self.subTest(order=order.order_id):
                self.assertRule("ORDER_NOT_ATTENDED", self.pack, order)
        self.assertRule("ORDER_NOT_FOUND", pack_bag, self.store, 999, by=ADMIN, photo="f.jpg", now=FRIDAY)

    # AR-E
    def test_ar_e_only_staff_packs(self):
        self.assertRule("NOT_AUTHORIZED", self.pack, self.first, by="vecino-1001")


class DeliverySpecTests(FulfillmentBase):
    # EN-A
    def test_en_a_zone_delivery_is_recorded(self):
        delivery = self.pack_and_deliver()
        self.assertEqual(sorted(delivery.order_ids), sorted(o.order_id for o in self.orders))
        self.assertEqual(delivery.received_by, "Sr. Ramos")
        self.assertEqual(delivery.delivered_at, SATURDAY)
        self.assertEqual(delivery.photo, "fotos/entrega.jpg")

    # EN-B
    def test_en_b_all_or_nothing(self):
        for order in self.orders[:7]:
            self.pack(order)
        self.assertRule("ORDERS_NOT_PACKED", self.deliver)
        self.assertNotIn((CYCLE, "Z-JM-01"), self.store.deliveries)

    # EN-C
    def test_en_c_delivery_requires_photo_and_receiver(self):
        for order in self.orders:
            self.pack(order)
        self.assertRule("PHOTO_REQUIRED", self.deliver, photo=" ")
        self.assertRule("RECEIVER_REQUIRED", self.deliver, received_by="")

    # EN-D
    def test_en_d_zone_is_delivered_once(self):
        self.pack_and_deliver()
        self.assertRule("ZONE_ALREADY_DELIVERED", self.deliver)

    # EN-E
    def test_en_e_invalid_zone_or_person(self):
        self.assertRule("NOTHING_TO_DELIVER", self.deliver, zone_id="Z-LINCE-02")
        self.assertRule("ZONE_NOT_FOUND", self.deliver, zone_id="Z-NO-EXISTE")
        self.assertRule("NOT_AUTHORIZED", self.deliver, by="vecino-1001")


class ClaimSpecTests(FulfillmentBase):
    # RC-A
    def test_rc_a_claim_in_time_is_pending(self):
        self.pack_and_deliver()
        before = wallet.balance(self.store, self.first.customer_id)
        claim = self.claim()
        self.assertEqual(claim.status, "PENDIENTE")
        self.assertEqual(claim.quantity, D("1"))
        self.assertEqual(wallet.balance(self.store, self.first.customer_id), before)

    # RC-B
    def test_rc_b_claim_window_is_24_hours(self):
        self.pack_and_deliver()
        self.assertRule("CLAIM_WINDOW_CLOSED", self.claim, now=SUNDAY_LATE)

    # RC-C
    def test_rc_c_order_must_be_delivered_and_own(self):
        self.assertRule("ORDER_NOT_DELIVERED", self.claim)
        self.pack_and_deliver()
        self.assertRule("ORDER_NOT_FOUND", self.claim, customer_id=self.orders[1].customer_id)

    # RC-D
    def test_rc_d_reason_and_photo(self):
        self.pack_and_deliver()
        self.assertRule("INVALID_CLAIM_REASON", self.claim, reason="OTRO")
        self.assertRule("PHOTO_REQUIRED", self.claim, photo="")

    # RC-E
    def test_rc_e_invalid_items(self):
        self.pack_and_deliver()
        for quantity, product_id in (("0", "CEBOLLA-ROJA"), ("1.5", "CEBOLLA-ROJA"), ("11", "CEBOLLA-ROJA"),
                                     ("abc", "CEBOLLA-ROJA"), ("1", "LIMON")):
            with self.subTest(quantity=quantity, product=product_id):
                self.assertRule("INVALID_CLAIM_ITEM", self.claim, quantity=quantity, product_id=product_id)
        self.claim("1")
        self.assertRule("INVALID_CLAIM_ITEM", self.claim, quantity="10")
        self.assertEqual(self.claim("9").quantity, D("9"))


class ReviewSpecTests(FulfillmentBase):
    # RV-A
    def test_rv_a_approved_claim_returns_the_article_as_balance(self):
        self.pack_and_deliver()
        claim = self.claim()
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        before = wallet.balance(self.store, self.first.customer_id)
        reviewed = review_claim(self.store, claim.claim_id, by=ADMIN, approve=True, now=SUNDAY_LATE)
        self.assertEqual(reviewed.status, "APROBADO")
        self.assertEqual(reviewed.refund_amount, D("2.02"))
        self.assertEqual(wallet.balance(self.store, self.first.customer_id), before + D("2.02"))

    # RV-B
    def test_rv_b_rejected_claim_moves_no_money(self):
        self.pack_and_deliver()
        claim = self.claim()
        before = wallet.balance(self.store, self.first.customer_id)
        reviewed = review_claim(self.store, claim.claim_id, by=ADMIN, approve=False, now=SUNDAY_IN_TIME)
        self.assertEqual(reviewed.status, "RECHAZADO")
        self.assertEqual(wallet.balance(self.store, self.first.customer_id), before)
        self.assertEqual(self.claim("10").quantity, D("10"))

    # RV-C
    def test_rv_c_approval_needs_settled_cycle(self):
        self.pack_and_deliver()
        claim = self.claim()
        self.assertRule("CYCLE_NOT_SETTLED", review_claim, self.store, claim.claim_id, by=ADMIN, approve=True,
                        now=SUNDAY_IN_TIME)

    # RV-D
    def test_rv_d_invalid_reviews(self):
        self.pack_and_deliver()
        claim = self.claim()
        self.assertRule("NOT_AUTHORIZED", review_claim, self.store, claim.claim_id, by="vecino-1001", approve=False,
                        now=SUNDAY_IN_TIME)
        review_claim(self.store, claim.claim_id, by=ADMIN, approve=False, now=SUNDAY_IN_TIME)
        self.assertRule("CLAIM_ALREADY_REVIEWED", review_claim, self.store, claim.claim_id, by=ADMIN, approve=True,
                        now=SUNDAY_IN_TIME)
        self.assertRule("CLAIM_NOT_FOUND", review_claim, self.store, 999, by=ADMIN, approve=True, now=SUNDAY_IN_TIME)

    # RV-E
    def test_rv_e_missing_item_is_not_returned_twice(self):
        self.pack_and_deliver()
        claim = self.claim()
        settle_cycle(self.store, CYCLE, [(self.first.order_id, "CEBOLLA-ROJA", "10")], at=SATURDAY)
        self.assertRule("INVALID_CLAIM_ITEM", review_claim, self.store, claim.claim_id, by=ADMIN, approve=True,
                        now=SUNDAY_IN_TIME)
        self.assertEqual(self.store.claims[claim.claim_id].status, "PENDIENTE")


class BufferSpecTests(FulfillmentBase):
    def add(self, product_id, quantity, by=ADMIN):
        return add_to_buffer(self.store, CYCLE, product_id, quantity, by=by)

    def cleaning_order(self):
        """Pedido con limpiatodo y lejía (más papa para el mínimo), en el grupo que se atiende."""
        return self.s.order("Z-JM-01", lines=[("LIMPIATODO-GALON", "4"), ("LEJIA-GALON", "1"),
                                                ("PAPA-AMARILLA", "5")]).order_id

    # CO-A
    def test_co_a_store_non_perishable_leftovers(self):
        stock = self.add("LIMPIATODO-GALON", "6")
        self.assertEqual(stock.quantity, D("6"))
        self.assertEqual(buffer_value(self.store), D("47.40"))

    # CO-B
    def test_co_b_buffer_has_amount_limit(self):
        self.add("LIMPIATODO-GALON", "60")
        self.add("LEJIA-GALON", "4")
        self.assertEqual(buffer_value(self.store), D("500.00"))
        self.assertRule("BUFFER_LIMIT_EXCEEDED", self.add, "LEJIA-GALON", "1")
        self.assertEqual(buffer_value(self.store), D("500.00"))

    # CO-C
    def test_co_c_invalid_products_or_quantities(self):
        self.assertRule("PERISHABLE_NOT_ALLOWED", self.add, "PAPA-AMARILLA", "5")
        self.assertRule("PRODUCT_NOT_AVAILABLE", self.add, "MANDARINA", "5")
        self.assertRule("INVALID_QUANTITY", self.add, "LIMPIATODO-GALON", "0")
        self.assertRule("INVALID_QUANTITY", self.add, "LIMPIATODO-GALON", "1.5")

    # CO-D
    def test_co_d_use_buffer_to_replace_missing_items(self):
        self.add("LIMPIATODO-GALON", "6")
        order = self.cleaning_order()  # S-122: cada uso indica el pedido
        stock = use_buffer(self.store, "LIMPIATODO-GALON", "2", order_id=order, by=ADMIN, now=FRIDAY)
        self.assertEqual(stock.quantity, D("4"))
        self.assertEqual(buffer_value(self.store), D("31.60"))
        self.assertRule("BUFFER_INSUFFICIENT", use_buffer, self.store, "LIMPIATODO-GALON", "5", order_id=order,
                        by=ADMIN, now=FRIDAY)
        self.assertRule("BUFFER_INSUFFICIENT", use_buffer, self.store, "LEJIA-GALON", "1", order_id=order,
                        by=ADMIN, now=FRIDAY)

    # CO-E
    def test_co_e_only_staff_uses_buffer(self):
        self.assertRule("NOT_AUTHORIZED", self.add, "LIMPIATODO-GALON", "6", by="vecino-1001")
        self.add("LIMPIATODO-GALON", "6")
        self.assertRule("NOT_AUTHORIZED", use_buffer, self.store, "LIMPIATODO-GALON", "1",
                        order_id=self.cleaning_order(), by="vecino-1001", now=FRIDAY)


if __name__ == "__main__":
    unittest.main()
