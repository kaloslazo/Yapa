"""Avisos de armado y liquidación: docs/propuestas/pulir-detalles.md."""

from datetime import timedelta
import unittest

from test_settlement import CYCLE, Scenario, buy_all
from yapa_sdd.cycle import closes_at
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import close_cycle, deliver_zone, pack_bag, register_failed_delivery
from yapa_sdd.purchase import register_damaged


class OperationMessagesTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)
        self.first = self.orders[0].order_id
        self.close = closes_at(CYCLE)
        self.before = self.close - timedelta(seconds=1)

    def test_bag_before_close_explains_purchases_and_does_not_save(self):
        with self.assertRaises(BusinessRuleError) as error:
            pack_bag(self.store, self.first, by="admin-yapa", photo="bolsa.jpg", now=self.before)
        self.assertEqual(error.exception.code, "CYCLE_STILL_OPEN")
        self.assertEqual(str(error.exception), "Todavía no puedes armar: esta semana sigue recibiendo compras. El armado se habilita el miércoles a las 8 p. m. (hora de Lima).")
        self.assertFalse(self.store.bags)

    def test_damaged_before_close_explains_when_to_register(self):
        with self.assertRaises(BusinessRuleError) as error:
            register_damaged(self.store, self.first, "CEBOLLA-ROJA", "1",
                             by="admin-yapa", photo="danado.jpg", now=self.before)
        self.assertEqual(error.exception.code, "CYCLE_STILL_OPEN")
        self.assertEqual(str(error.exception), "Todavía no puedes registrar productos dañados: esta semana sigue recibiendo compras. El armado se habilita el miércoles a las 8 p. m. (hora de Lima).")
        self.assertFalse(self.store.shortages)

    def test_bag_at_close_is_allowed(self):
        bag = pack_bag(self.store, self.first, by="admin-yapa", photo="bolsa.jpg", now=self.close)
        self.assertEqual(bag.number, 1)
        self.assertEqual(bag.photo, "bolsa.jpg")

    def test_pending_zones_message_is_specific_and_sorted(self):
        self.s.orders("Z-LINCE-01", 8)
        with self.assertRaises(BusinessRuleError) as error:
            close_cycle(self.store, CYCLE, at=self.close)
        self.assertEqual(error.exception.code, "ZONES_PENDING")
        self.assertEqual(str(error.exception), "Entrega pendiente de registrar en: Z-JM-01, Z-LINCE-01.")
        self.assertFalse(self.store.bags)

    def test_delivered_zone_is_not_reported_as_pending(self):
        self.s.orders("Z-LINCE-01", 8)
        for order in self.orders:
            pack_bag(self.store, order.order_id, by="admin-yapa", photo="bolsa.jpg", now=self.close)
        buy_all(self.store, CYCLE)
        deliver_zone(self.store, CYCLE, "Z-JM-01", by="admin-yapa", photo="entrega.jpg",
                     received_by="Portería", now=self.close)
        with self.assertRaises(BusinessRuleError) as error:
            close_cycle(self.store, CYCLE, at=self.close)
        self.assertEqual(error.exception.code, "ZONES_PENDING")
        self.assertIn("Z-LINCE-01", str(error.exception))
        self.assertNotIn("Z-JM-01", str(error.exception))

    def test_registered_failed_delivery_allows_settlement(self):
        for order in self.orders:
            pack_bag(self.store, order.order_id, by="admin-yapa", photo="bolsa.jpg", now=self.close)
        buy_all(self.store, CYCLE)
        register_failed_delivery(self.store, CYCLE, "Z-JM-01", by="admin-yapa",
                                 photo="puerta.jpg", reason="NADIE_RECIBE", now=self.close)
        result = close_cycle(self.store, CYCLE, at=self.close)
        self.assertTrue(result.orders)
        self.assertTrue(all(order.status == "NO_ENTREGADO" for order in result.orders.values()))
