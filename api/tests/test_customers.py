"""Criterios de la iteración 24 (docs/desarrollo/24-alta-vecinos.md)."""

from datetime import datetime
import re
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd.auth import authenticate, set_admin_password, set_pin
from yapa_sdd.customers import register_customer, reset_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
ADMIN, ADMIN_PASS = "admin-yapa", "yapa-admin-2026"
PHONE = "987654321"


class CustomerBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()

    def register(self, name="Lucía Ramos", phone=PHONE, zone_id="Z-LINCE-01", consent=True, by=ADMIN, email=None):
        return register_customer(self.store, name, phone, zone_id, consent, by=by, now=NOW, email=email or f"{phone}@correo.pe")

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def assertValidPin(self, pin):
        self.assertRegex(pin, r"^\d{6}$")
        steps = {int(b) - int(a) for a, b in zip(pin, pin[1:])}
        self.assertNotIn(steps, ({0}, {1}, {-1}))


class RegisterCustomerTests(CustomerBase):
    # AV-A
    def test_av_a_register_new_neighbor(self):
        customer, pin = self.register()
        self.assertEqual(customer.customer_id, 106)
        self.assertEqual((customer.name, customer.phone, customer.zone_id, customer.consent_at),
                         ("Lucía Ramos", PHONE, "Z-LINCE-01", NOW))
        self.assertIs(self.store.customers[106], customer)
        self.assertValidPin(pin)
        self.assertEqual(authenticate(self.store, "vecino", 106, pin, NOW), 106)

    def test_av06_generated_pins_are_always_valid(self):
        for i in range(40):
            _, pin = self.register(phone=f"9{i:08d}")
            self.assertValidPin(pin)

    # AV-B
    def test_av_b_invalid_data_creates_nothing(self):
        self.assertRule("NAME_REQUIRED", self.register, name="   ")
        self.assertRule("INVALID_PHONE", self.register, phone="98765432")
        self.assertRule("INVALID_PHONE", self.register, phone="887654321")
        self.assertRule("ZONE_NOT_FOUND", self.register, zone_id="Z-NO-EXISTE")
        self.assertRule("CONSENT_REQUIRED", self.register, consent=False)
        self.assertRule("NOT_AUTHORIZED", self.register, by="vecino-101")
        self.assertNotIn(106, self.store.customers)

    # AV-C
    def test_av_c_phone_is_unique(self):
        self.register()
        self.assertRule("PHONE_ALREADY_REGISTERED", self.register, name="Otra persona")
        self.assertNotIn(107, self.store.customers)

    # AV-D
    def test_av_d_pin_is_not_stored(self):
        _, pin = self.register()
        credential = self.store.credentials[("vecino", "106")]
        self.assertNotEqual(credential.hash, pin.encode())
        self.assertNotIn(pin, repr(self.store.customers[106]))

    # AV-E
    def test_av_e_reset_pin_unlocks_account(self):
        _, old_pin = self.register()
        wrong = "000000" if old_pin != "000000" else "111111"
        for _ in range(5):
            self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "vecino", 106, wrong, NOW)
        self.assertRule("ACCOUNT_LOCKED", authenticate, self.store, "vecino", 106, old_pin, NOW)
        new_pin = reset_pin(self.store, 106, by=ADMIN)
        self.assertValidPin(new_pin)
        self.assertEqual(authenticate(self.store, "vecino", 106, new_pin, NOW), 106)
        if new_pin != old_pin:
            self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "vecino", 106, old_pin, NOW)
        self.assertRule("CUSTOMER_NOT_FOUND", reset_pin, self.store, 999, by=ADMIN)
        self.assertRule("NOT_AUTHORIZED", reset_pin, self.store, 106, by="vecino-101")


class CustomerWebTests(CustomerBase):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: NOW)
        self.admin = WebClient(self.app)
        self.admin.login(ADMIN, ADMIN_PASS, kind="admin")

    def post_register(self, client=None, **overrides):
        data = {"nombre": "Lucía Ramos", "celular": PHONE, "zona": "Z-LINCE-01", "consentimiento": "si", "correo": "lucia@correo.pe"}
        data.update(overrides)
        return (client or self.admin).post("/admin/vecinos", data)

    # AV-G
    def test_av_g_register_from_web_and_list(self):
        status, _, html = self.post_register()
        self.assertEqual(status, 200)
        self.assertIn("Cliente 106", html)
        pin = re.search(r"PIN: (\d{6})", html).group(1)
        neighbor = WebClient(self.app)
        neighbor.login(106, pin)
        self.assertEqual(neighbor.get("/cuenta")[0], 200)
        status, _, listing = self.admin.get("/admin/vecinos")
        self.assertEqual(status, 200)
        self.assertIn("Lucía Ramos", listing)
        self.assertIn(PHONE, listing)
        self.assertNotIn(pin, listing)  # AV-D

    def test_av05_missing_consent_from_web(self):
        status, _, html = self.post_register(consentimiento="")
        self.assertEqual(status, 422)
        self.assertIn("CONSENT_REQUIRED", html)

    def test_av07_reset_pin_from_web(self):
        self.post_register()
        status, _, html = self.admin.post("/admin/vecinos/pin", {"cliente": "106"})
        self.assertEqual(status, 200)
        pin = re.search(r"PIN: (\d{6})", html).group(1)
        self.assertEqual(authenticate(self.store, "vecino", 106, pin, NOW), 106)

    # AV-F
    def test_av_f_neighbor_forbidden(self):
        set_pin(self.store, 101, "482915")
        neighbor = WebClient(self.app)
        neighbor.login(101, "482915")
        self.assertEqual(neighbor.get("/admin/vecinos")[0], 403)
        self.assertEqual(self.post_register(client=neighbor)[0], 403)
        self.assertNotIn(106, self.store.customers)


if __name__ == "__main__":
    unittest.main()
