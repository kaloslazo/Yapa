"""Iteración 71: bolsa con su revisión y baja de una bolsa. Spec: docs/desarrollo/71-armado-unificado.md."""
import tempfile
import unittest
from pathlib import Path

from test_fulfillment import BEFORE_CLOSE, FRIDAY
from test_settlement import CYCLE, Scenario
from yapa_sdd import fulfillment, persistence
from yapa_sdd.domain import BusinessRuleError


class BagReviewTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.order = self.s.orders("Z-JM-01", 8)[0]

    def pack(self, photo, review=(), now=FRIDAY):
        return fulfillment.pack_bag(self.store, self.order.order_id, by="admin-yapa", photo=photo, now=now, review=review)

    def test_ar71_a_review_survives_a_restart_and_removal_keeps_the_numbers(self):
        first = self.pack("uno.jpg", [{"id": "PAPA-AMARILLA", "unidades": 2}])
        second = self.pack("dos.jpg")
        fulfillment.remove_bag(self.store, self.order.order_id, first.number, by="admin-yapa", now=FRIDAY)
        third = self.pack("tres.jpg")
        self.assertEqual((second.number, third.number), (2, 3))
        self.assertEqual(len(self.store.bag_removals), 1)
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "test.db")
            persistence.save(self.store, path)
            loaded = persistence.load(path)
        self.assertEqual(loaded.bag_removals[0]["foto"], "uno.jpg")

    def test_ar71_b_foreign_product_or_bad_count_saves_no_bag(self):
        for row in [{"id": "NO-EXISTE", "unidades": 1}, {"id": "PAPA-AMARILLA", "unidades": 0},
                    {"id": "PAPA-AMARILLA", "unidades": 1.5}]:
            with self.assertRaises(BusinessRuleError) as e:
                self.pack("x.jpg", [row])
            self.assertEqual(e.exception.code, "INVALID_BAG_REVIEW")
        self.assertFalse(self.store.bags)

    def test_ar71_c_no_removal_after_dispatch_and_no_packing_before_close(self):
        bag = self.pack("x.jpg")
        self.store.dispatches[(CYCLE, "Z-JM-01")] = object()
        with self.assertRaises(BusinessRuleError) as e:
            fulfillment.remove_bag(self.store, self.order.order_id, bag.number, by="admin-yapa", now=FRIDAY)
        self.assertEqual(e.exception.code, "ZONE_ALREADY_CLOSED")
        self.assertEqual(len(self.store.bags[self.order.order_id]), 1)
        with self.assertRaises(BusinessRuleError) as e:
            self.pack("x.jpg", now=BEFORE_CLOSE)
        self.assertEqual(e.exception.code, "CYCLE_STILL_OPEN")

    def test_ar71_d_unknown_bag_has_a_clear_error(self):
        with self.assertRaises(BusinessRuleError) as e:
            fulfillment.remove_bag(self.store, self.order.order_id, 99, by="admin-yapa", now=FRIDAY)
        self.assertEqual(e.exception.code, "BAG_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
