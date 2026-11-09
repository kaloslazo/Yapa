"""Iteración 57 · 25 % del ahorro retenido y retiro del consentimiento.

Spec: docs/desarrollo/57-ahorro-retenido-y-retiro-de-datos.md.
"""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_settlement import BASKET, CYCLE, NOW, Scenario
from web_client import fast_hashing

from yapa_sdd import customers, notices, purchase, wallet
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.claims import Claim
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import OPERATING_SAVINGS_SHARE, close_cycle, deliver_zone, pack_bag
from yapa_sdd.invitations import _create
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.api import create_api


ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
CARMEN = 105


class SavingsShareTests(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.s.orders("Z-JM-01", 8)

    # AH-A
    def test_ah_a_operating_settlement_keeps_25_percent(self):
        self.assertEqual(OPERATING_SAVINGS_SHARE, D("0.25"))
        purchase.register_purchase(self.store, CYCLE, {}, by=ADMIN, now=FRIDAY)
        for order_id in range(1, 9):
            pack_bag(self.store, order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)
        deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/e.jpg", received_by="Sr. Ramos", now=SATURDAY)
        result = close_cycle(self.store, CYCLE, at=SATURDAY)
        self.assertEqual(result.products["CEBOLLA-ROJA"].final_unit_price, D("2.100"))

    def test_ah_a_pure_settlement_still_zero_by_default(self):
        result = settle_cycle(self.store, CYCLE)
        self.assertEqual(result.products["CEBOLLA-ROJA"].final_unit_price, D("2.016"))


class WithdrawSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.store.customers[CARMEN] = replace(self.store.customers[CARMEN], email="carmen@correo.pe", phone="987654321",
                                               consent_at=NOW, google_sub="g-123")
        set_pin(self.store, CARMEN, PIN)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def withdraw(self, confirmation="RETIRAR", customer_id=CARMEN):
        return customers.withdraw_consent(self.store, customer_id, confirmation, now=FRIDAY)

    # RD-A
    def test_rd_a_anonymizes_and_keeps_money_records(self):
        token = _create(self.store, CARMEN, NOW)
        notices.add(self.store, CARMEN, "PRUEBA", "Hola", "Aviso", NOW)
        customers.request_pin_help(self.store, str(CARMEN), NOW)
        wallet.credit(self.store, CARMEN, D("5"), "ABONO_LIQUIDACION", NOW, "pedido 1")
        wallet.request_withdrawal(self.store, CARMEN, D("5"), NOW)
        refund = next(iter(self.store.refunds.values()))
        wallet.mark_refund_paid(self.store, refund.refund_id, "OP-1")
        movements = len(self.store.movements)

        customer = self.withdraw()
        self.assertEqual(customer.name, "Vecino retirado")
        for field in ("phone", "email", "lat", "lon", "google_sub", "consent_at", "email_verified_at"):
            self.assertIsNone(getattr(customer, field), field)
        self.assertTrue(customer.suspended)
        self.assertFalse(customer.email_notices)
        self.assertEqual(customer.withdrawn_at, FRIDAY)
        self.assertNotIn(("vecino", str(CARMEN)), self.store.credentials)
        self.assertFalse(self.store.invites[token]["active"])
        self.assertEqual(notices.for_customer(self.store, CARMEN), [])
        self.assertFalse(any(c == CARMEN for c, _ in self.store.pin_requests.values()))
        self.assertEqual(len(self.store.movements), movements)
        self.assertIn(refund.refund_id, self.store.refunds)

    # RD-B
    def test_rd_b_blocked_cases(self):
        self.assertRule("CONFIRMATION_REQUIRED", self.withdraw, "retirar")
        self.assertRule("CONFIRMATION_REQUIRED", self.withdraw, "")
        wallet.credit(self.store, CARMEN, D("5"), "ABONO_LIQUIDACION", NOW, "pedido 1")
        self.assertRule("BALANCE_PENDING", self.withdraw)
        wallet.request_withdrawal(self.store, CARMEN, D("5"), NOW)
        self.assertRule("BALANCE_PENDING", self.withdraw)  # devolución pendiente
        refund = next(iter(self.store.refunds.values()))
        wallet.mark_refund_paid(self.store, refund.refund_id, "OP-1")
        self.store.claims[1] = Claim(1, 1, CARMEN, "CEBOLLA-ROJA", D("1"), "DANADO", "f.jpg", NOW)
        self.assertRule("CLAIM_PENDING", self.withdraw)
        del self.store.claims[1]
        zone = self.store.zones["Z-LINCE-01"]
        zone.admin_id = CARMEN
        self.assertRule("ZONE_ADMIN_MUST_TRANSFER", self.withdraw)
        zone.admin_id = None
        self.withdraw()

    def test_rd_b_active_order_blocks(self):
        order = self.s.order("Z-JM-01", lines=BASKET)
        self.assertRule("HAS_ACTIVE_ORDER", self.withdraw, customer_id=order.customer_id)

    # RD-C
    def test_rd_c_cannot_log_in_or_withdraw_again(self):
        self.withdraw()
        self.assertRule("CUSTOMER_NOT_FOUND", self.withdraw)
        for user in ("carmen@correo.pe", "987654321"):  # S-245: igual que un usuario que no existe
            self.assertEqual(customers.resolve_login(self.store, user), "0")


class WithdrawApiTests(unittest.TestCase):
    # RD-D
    def test_rd_d_api_closes_the_session(self):
        fast_hashing(self)
        store = Scenario().store
        set_admin_password(store, ADMIN, ADMIN_PASS)
        set_pin(store, CARMEN, PIN)
        api = create_api(store, clock=lambda: FRIDAY, security_clock=lambda: FRIDAY)
        client = ApiClient(api)
        self.assertEqual(client.login(CARMEN, PIN)[0], 200)
        self.assertEqual(client.post("/api/cuenta/retirar-consentimiento", {"confirmar": "no"})[0], 422)
        status, data, _ = client.post("/api/cuenta/retirar-consentimiento", {"confirmar": "RETIRAR"})
        self.assertEqual(status, 200)
        self.assertEqual(client.get("/api/mis-pedidos")[0], 401)


if __name__ == "__main__":
    unittest.main()
