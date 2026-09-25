from datetime import datetime, timedelta
from decimal import Decimal
import unittest

from test_settlement import BASKET, CYCLE, Scenario

from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.order_registration import quote_order, register_order, verify_payment
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import amount_owed, balance, credit, mark_refund_paid, request_withdrawal


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
NEXT_WEEK = datetime(2026, 9, 21, 10, 0, tzinfo=LIMA)  # lunes del ciclo 2026-W39

CA01_LINES = [("PAPA-AMARILLA", "5"), ("CEBOLLA-ROJA", "3"), ("LIMON", "2"), ("AJO", "1"), ("LIMPIATODO-GALON", "2")]


def pay(store, customer_id, *, use_balance, amount, method="YAPE", code="OP-B1", lines=CA01_LINES, now=NOW):
    return register_order(
        store,
        customer_id=customer_id,
        lines=lines,
        payment_method=method,
        operation_code=code,
        amount=amount,
        use_balance=use_balance,
        now=now,
    )


class WalletSpecTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def settled_customer(self):
        """Ciclo del CL-04: al primer vecino le vuelven S/ 12.86."""
        orders = self.s.orders("Z-JM-01", 20)
        settle_cycle(self.store, CYCLE)
        return orders[0].customer_id

    # CB-01
    def test_cb01_settlement_credits_balance(self):
        customer_id = self.settled_customer()
        self.assertEqual(balance(self.store, customer_id), Decimal("12.86"))

    # CB-02
    def test_cb02_partial_balance_plus_yape(self):
        customer_id = self.settled_customer()
        order = pay(self.store, customer_id, use_balance=Decimal("12.86"), amount=Decimal("46.65"), now=NEXT_WEEK)
        self.assertEqual(order.total, Decimal("59.51"))
        self.assertEqual([p.method for p in order.payments], ["SALDO", "YAPE"])
        self.assertEqual(order.payment_status, "POR_VERIFICAR")
        self.assertEqual(balance(self.store, customer_id), Decimal("0"))

    # CB-03
    def test_cb03_balance_covers_everything(self):
        credit(self.store, 101, Decimal("70"), "ABONO_LIQUIDACION", NOW)
        order = pay(self.store, 101, use_balance=Decimal("59.51"), amount=Decimal("0"), method=None, code=None)
        self.assertEqual(order.payment_status, "VERIFICADO")
        self.assertEqual(order.payment_method, "SALDO")
        self.assertEqual(balance(self.store, 101), Decimal("10.49"))

    # CB-04
    def test_cb04_rejects_more_than_available(self):
        credit(self.store, 101, Decimal("5"), "ABONO_LIQUIDACION", NOW)
        self.assertRule("INSUFFICIENT_BALANCE", pay, self.store, 101, use_balance=Decimal("10"),
                        amount=Decimal("49.51"))
        self.assertEqual(balance(self.store, 101), Decimal("5"))

    def test_cb04_rejects_negative_balance_use(self):
        self.assertRule("INSUFFICIENT_BALANCE", pay, self.store, 101, use_balance=Decimal("-1"),
                        amount=Decimal("60.51"))

    # CB-05
    def test_cb05_rejects_balance_above_total(self):
        credit(self.store, 101, Decimal("100"), "ABONO_LIQUIDACION", NOW)
        self.assertRule("BALANCE_EXCEEDS_TOTAL", pay, self.store, 101, use_balance=Decimal("60"),
                        amount=Decimal("0"))

    # CB-06
    def test_cb06_external_amount_must_be_the_rest(self):
        credit(self.store, 101, Decimal("12.86"), "ABONO_LIQUIDACION", NOW)
        self.assertRule("PAYMENT_AMOUNT_MISMATCH", pay, self.store, 101, use_balance=Decimal("12.86"),
                        amount=Decimal("59.51"))

    # CB-07
    def test_cb07_balance_does_not_expire(self):
        credit(self.store, 101, Decimal("12.86"), "ABONO_LIQUIDACION", NOW - timedelta(days=400))
        order = pay(self.store, 101, use_balance=Decimal("12.86"), amount=Decimal("46.65"))
        self.assertEqual(order.payments[0].amount, Decimal("12.86"))

    # CB-08
    def test_cb08_not_served_zone_splits_refund(self):
        self.s.orders("Z-JM-01", 6)
        self.store.add_customer(Customer(2001, "Vecina con saldo", "Z-JM-01"))
        credit(self.store, 2001, Decimal("10"), "ABONO_LIQUIDACION", NOW)
        order = pay(self.store, 2001, use_balance=Decimal("10"), amount=Decimal("51.00"), lines=BASKET)
        verify_payment(self.store, order.order_id, now=NOW)
        result = settle_cycle(self.store, CYCLE)
        settled = result.orders[order.order_id]
        self.assertEqual(settled.status, "NO_ATENDIDO")
        self.assertEqual(settled.refund_amount, Decimal("51.00"))
        self.assertEqual(settled.refund_destination, "MEDIO_DE_PAGO")
        self.assertEqual(settled.returned_to_balance, Decimal("10"))
        self.assertEqual(balance(self.store, 2001), Decimal("10"))
        pending = [r for r in self.store.refunds.values() if r.customer_id == 2001]
        self.assertEqual([r.amount for r in pending], [Decimal("51.00")])

    # CB-09
    def test_cb09_cancelled_order_returns_balance_part(self):
        self.s.orders("Z-JM-01", 8)
        credit(self.store, 101, Decimal("12.86"), "ABONO_LIQUIDACION", NOW)
        order = pay(self.store, 101, use_balance=Decimal("12.86"), amount=Decimal("46.65"))
        result = settle_cycle(self.store, CYCLE)
        self.assertEqual(result.orders[order.order_id].status, "CANCELADO")
        self.assertEqual(balance(self.store, 101), Decimal("12.86"))

    # CB-10
    def test_cb10_cycle_is_settled_only_once(self):
        customer_id = self.settled_customer()
        self.assertRule("CYCLE_ALREADY_SETTLED", settle_cycle, self.store, CYCLE)
        self.assertEqual(balance(self.store, customer_id), Decimal("12.86"))

    # CB-11
    def test_cb11_withdrawal_request(self):
        customer_id = self.settled_customer()
        refund = request_withdrawal(self.store, customer_id, Decimal("10"), datetime(2026, 9, 20, 9, 0, tzinfo=LIMA))
        self.assertEqual(balance(self.store, customer_id), Decimal("2.86"))
        self.assertEqual(refund.status, "PENDIENTE")
        self.assertEqual(refund.due_date.date(), datetime(2026, 10, 20).date())

    # CB-12
    def test_cb12_invalid_withdrawals(self):
        credit(self.store, 101, Decimal("5"), "ABONO_LIQUIDACION", NOW)
        self.assertRule("INVALID_AMOUNT", request_withdrawal, self.store, 101, Decimal("0"), NOW)
        self.assertRule("INSUFFICIENT_BALANCE", request_withdrawal, self.store, 101, Decimal("5.01"), NOW)

    # CB-13
    def test_cb13_admin_pays_refund_once(self):
        credit(self.store, 101, Decimal("5"), "ABONO_LIQUIDACION", NOW)
        refund = request_withdrawal(self.store, 101, Decimal("5"), NOW)
        paid = mark_refund_paid(self.store, refund.refund_id, "YP-99881")
        self.assertEqual(paid.status, "PAGADO")
        self.assertRule("REFUND_ALREADY_PAID", mark_refund_paid, self.store, refund.refund_id, "YP-99882")
        self.assertRule("REFUND_NOT_FOUND", mark_refund_paid, self.store, 999, "YP-1")

    # CB-14
    def test_cb14_total_owed_to_customers(self):
        credit(self.store, 101, Decimal("12.86"), "ABONO_LIQUIDACION", NOW)
        credit(self.store, 105, Decimal("12.86"), "ABONO_LIQUIDACION", NOW)
        request_withdrawal(self.store, 105, Decimal("10"), NOW)
        self.assertEqual(amount_owed(self.store), Decimal("25.72"))


if __name__ == "__main__":
    unittest.main()
