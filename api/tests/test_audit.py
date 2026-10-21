from datetime import datetime
from decimal import Decimal as D
import unittest

from test_settlement import CYCLE, Scenario

from yapa_sdd.audit import money_balance
from yapa_sdd.cycle import LIMA
from yapa_sdd.order_changes import edit_order
from yapa_sdd.order_registration import register_order, verify_payment
from yapa_sdd.seed import pilot_store
from yapa_sdd.settlement import settle_cycle


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)


class AuditSpecTests(unittest.TestCase):
    # AU-A
    def test_au_a_simple_order_and_settlement(self):
        s = Scenario()
        s.order("Z-JM-01")
        balance = money_balance(s.store)
        self.assertEqual((balance.received, balance.in_flight, balance.kept, balance.owed),
                         (D("61.00"), D("61.00"), D("0"), D("0")))
        self.assertEqual(balance.difference, D("0"))
        s.orders("Z-JM-01", 7)
        settle_cycle(s.store, CYCLE)
        balance = money_balance(s.store)
        self.assertEqual(balance.received, D("488.00"))
        self.assertEqual(balance.difference, D("0"))

    def test_au01_verifying_twice_does_not_duplicate_cash(self):
        s = Scenario()
        order = s.order("Z-JM-01")
        verify_payment(s.store, order.order_id, now=NOW)
        self.assertEqual(len(s.store.cash_in), 1)

    # AU-B
    def test_au_b_edit_down_keeps_received_amount(self):
        store = pilot_store()
        order = register_order(store, customer_id=101, lines=[("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "4")],
                               payment_method="YAPE", operation_code="AU-B", amount=D("59.60"), now=NOW)
        verify_payment(store, order.order_id, now=NOW)
        edit_order(store, order.order_id, customer_id=101, now=NOW,
                   lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "3")])
        balance = money_balance(store)
        self.assertEqual(balance.received, D("59.60"))
        self.assertEqual(balance.owed, D("4.58"))
        self.assertEqual(balance.difference, D("0"))


if __name__ == "__main__":
    unittest.main()
