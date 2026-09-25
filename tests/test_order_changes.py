from datetime import datetime
from decimal import Decimal
import unittest

from test_settlement import CYCLE, Scenario

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.order_changes import cancel_order, edit_order
from yapa_sdd.order_registration import register_order, verify_payment
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import balance, credit


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
CLOSE = datetime(2026, 9, 16, 20, 0, tzinfo=LIMA)
BASE = [("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "4")]  # total S/ 59.60


class OrderChangesSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def base_order(self, customer_id=101, verified=True, use_balance=Decimal("0"), code="OP-BASE"):
        order = register_order(self.store, customer_id=customer_id, lines=BASE, payment_method="YAPE",
                               operation_code=code, amount=Decimal("59.60") - use_balance,
                               use_balance=use_balance, now=NOW)
        if verified:
            verify_payment(self.store, order.order_id, now=NOW)
        return order

    def pending_refunds(self, customer_id):
        return [r.amount for r in self.store.refunds.values()
                if r.customer_id == customer_id and r.status == "PENDIENTE"]

    # CC-01
    def test_cc01_cancel_refunds_to_payment_method(self):
        order = self.base_order()
        cancel_order(self.store, order.order_id, customer_id=101, refund_to="MEDIO_DE_PAGO", now=NOW)
        self.assertEqual(self.store.orders[order.order_id].status, "CANCELADO_POR_CLIENTE")
        self.assertEqual(self.pending_refunds(101), [Decimal("59.60")])
        self.assertEqual(self.store.reserved_quantity("PAPA-AMARILLA"), Decimal("0"))

    # CC-02
    def test_cc02_cancel_refunds_to_balance(self):
        order = self.base_order()
        cancel_order(self.store, order.order_id, customer_id=101, refund_to="SALDO", now=NOW)
        self.assertEqual(balance(self.store, 101), Decimal("59.60"))
        self.assertEqual(self.pending_refunds(101), [])

    # CC-03
    def test_cc03_cancel_mixed_payment(self):
        credit(self.store, 101, Decimal("10"), "ABONO_LIQUIDACION", NOW)
        order = self.base_order(use_balance=Decimal("10"))
        cancel_order(self.store, order.order_id, customer_id=101, refund_to="MEDIO_DE_PAGO", now=NOW)
        self.assertEqual(balance(self.store, 101), Decimal("10"))
        self.assertEqual(self.pending_refunds(101), [Decimal("49.60")])

    # CC-04
    def test_cc04_cancel_unverified_has_no_automatic_refund(self):
        order = self.base_order(verified=False)
        cancel_order(self.store, order.order_id, customer_id=101, refund_to="MEDIO_DE_PAGO", now=NOW)
        self.assertEqual(self.store.orders[order.order_id].status, "CANCELADO_POR_CLIENTE")
        self.assertEqual(self.pending_refunds(101), [])

    # CC-05
    def test_cc05_cannot_cancel_after_close(self):
        order = self.base_order()
        self.assertRule("CYCLE_CLOSED", cancel_order, self.store, order.order_id, customer_id=101, now=CLOSE)

    # CC-06
    def test_cc06_only_owner_can_cancel(self):
        order = self.base_order()
        self.assertRule("ORDER_NOT_FOUND", cancel_order, self.store, order.order_id, customer_id=105, now=NOW)

    # CC-07
    def test_cc07_cannot_cancel_twice(self):
        order = self.base_order()
        cancel_order(self.store, order.order_id, customer_id=101, now=NOW)
        self.assertRule("ORDER_NOT_EDITABLE", cancel_order, self.store, order.order_id, customer_id=101, now=NOW)

    # CC-08
    def test_cc08_new_order_after_cancel_but_code_not_reused(self):
        order = self.base_order()
        cancel_order(self.store, order.order_id, customer_id=101, now=NOW)
        with self.assertRaises(BusinessRuleError) as raised:
            self.base_order(code="OP-BASE")
        self.assertEqual(raised.exception.code, "PAYMENT_CODE_ALREADY_USED")
        again = self.base_order(code="OP-NUEVO")
        self.assertEqual(again.status, "REGISTRADO")

    # CC-09
    def test_cc09_invalid_refund_destination(self):
        order = self.base_order()
        self.assertRule("INVALID_REFUND_DESTINATION", cancel_order, self.store, order.order_id, customer_id=101,
                        refund_to="TARJETA", now=NOW)
        self.assertEqual(self.store.orders[order.order_id].status, "REGISTRADO")

    # CC-10
    def test_cc10_settlement_ignores_cancelled_orders(self):
        orders = self.s.orders("Z-JM-01", 8)
        victim = orders[0]
        cancel_order(self.store, victim.order_id, customer_id=victim.customer_id, now=NOW)
        result = settle_cycle(self.store, CYCLE)
        self.assertNotIn(victim.order_id, result.orders)
        self.assertEqual(result.orders[orders[1].order_id].status, "NO_ATENDIDO")
        self.assertEqual(len(self.pending_refunds(victim.customer_id)), 1)

    # CE-A
    def test_ce_a_edit_down_returns_difference_to_balance(self):
        order = self.base_order()
        edited = edit_order(self.store, order.order_id, customer_id=101, now=NOW,
                            lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "3")])
        self.assertEqual(edited.total, Decimal("55.02"))
        self.assertEqual(balance(self.store, 101), Decimal("4.58"))
        self.assertEqual(sum(p.amount for p in edited.payments), Decimal("55.02"))
        self.assertEqual(self.store.reserved_quantity("LIMPIATODO-GALON"), Decimal("3"))
        self.assertEqual(self.store.reserved_quantity("PAPA-AMARILLA"), Decimal("6"))

    # CE-B
    def test_ce_b_edit_up_requires_paying_the_difference(self):
        order = self.base_order()
        edited = edit_order(self.store, order.order_id, customer_id=101, now=NOW,
                            lines=[("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "5")],
                            payment_method="PLIN", operation_code="PL-DIF1", amount=Decimal("8.61"))
        self.assertEqual(edited.total, Decimal("68.21"))
        self.assertEqual(edited.payments[-1].amount, Decimal("8.61"))
        self.assertEqual(edited.payment_status, "POR_VERIFICAR")

    # CE-C
    def test_ce_c_wrong_difference_leaves_order_unchanged(self):
        order = self.base_order()
        self.assertRule("PAYMENT_AMOUNT_MISMATCH", edit_order, self.store, order.order_id, customer_id=101, now=NOW,
                        lines=[("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "5")],
                        payment_method="PLIN", operation_code="PL-DIF1", amount=Decimal("8.00"))
        same = self.store.orders[order.order_id]
        self.assertEqual(same.total, Decimal("59.60"))
        self.assertEqual(self.store.reserved_quantity("LIMPIATODO-GALON"), Decimal("4"))
        self.assertNotIn("PL-DIF1", self.store.used_codes)

    # CE-D
    def test_ce_d_edit_below_minimum_is_rejected(self):
        order = self.base_order()
        self.assertRule("SUBTOTAL_BELOW_MINIMUM", edit_order, self.store, order.order_id, customer_id=101, now=NOW,
                        lines=[("LIMPIATODO-GALON", "5")])
        self.assertEqual(self.store.orders[order.order_id].total, Decimal("59.60"))
        self.assertEqual(self.store.reserved_quantity("PAPA-AMARILLA"), Decimal("5"))

    # CE-E
    def test_ce_e_own_reservation_counts_as_available(self):
        self.store.reserve("PAPA-AMARILLA", Decimal("395"))
        order = self.base_order()
        edited = edit_order(self.store, order.order_id, customer_id=101, now=NOW,
                            lines=[("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "5")],
                            payment_method="YAPE", operation_code="OP-DIF2", amount=Decimal("8.61"))
        self.assertEqual(edited.lines[0].quantity, Decimal("5"))
        self.assertRule("PRODUCT_SOLD_OUT", edit_order, self.store, order.order_id, customer_id=101, now=NOW,
                        lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "5")],
                        payment_method="YAPE", operation_code="OP-DIF3", amount=Decimal("4.03"))

    # CE-F
    def test_ce_f_cannot_edit_after_close(self):
        order = self.base_order()
        self.assertRule("CYCLE_CLOSED", edit_order, self.store, order.order_id, customer_id=101, now=CLOSE,
                        lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "3")])

    # CE-G
    def test_ce_g_not_served_after_edit_down_returns_everything(self):
        order = self.base_order()
        edit_order(self.store, order.order_id, customer_id=101, now=NOW,
                   lines=[("PAPA-AMARILLA", "6"), ("LIMPIATODO-GALON", "3")])
        result = settle_cycle(self.store, CYCLE)
        settled = result.orders[order.order_id]
        self.assertEqual(settled.status, "NO_ATENDIDO")
        self.assertEqual(settled.refund_amount, Decimal("55.02"))
        self.assertEqual(settled.refund_amount + balance(self.store, 101), Decimal("59.60"))


if __name__ == "__main__":
    unittest.main()
