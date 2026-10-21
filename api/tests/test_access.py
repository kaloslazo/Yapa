from datetime import datetime, timedelta
from decimal import Decimal
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd.auth import authenticate, change_pin, set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
PIN = "482915"
ADMIN_PASS = "yapa-admin-2026"
CA01 = {"cant_PAPA-AMARILLA": "5", "cant_CEBOLLA-ROJA": "3", "cant_LIMON": "2", "cant_AJO": "1",
        "cant_LIMPIATODO-GALON": "2"}


class AccessSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_pin(self.store, 105, "739104")
        set_admin_password(self.store, "admin-yapa", ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: NOW)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    # AA-01
    def test_aa01_pin_is_stored_hashed(self):
        stored = self.store.credentials[("vecino", "101")]
        self.assertNotIn(PIN.encode(), stored.hash)
        self.assertNotEqual(stored.hash, PIN)
        self.assertEqual(len(stored.salt), 16)

    # AA-02
    def test_aa02_invalid_pins(self):
        for pin in ("12345", "1234567", "abcdef", "111111", "123456", "654321"):
            with self.subTest(pin=pin):
                self.assertRule("INVALID_PIN", set_pin, self.store, 101, pin)

    # AA-03
    def test_aa03_login_and_same_error_for_unknown(self):
        self.assertEqual(authenticate(self.store, "vecino", "101", PIN, NOW), 101)
        self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "vecino", "101", "000001", NOW)
        self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "vecino", "999", PIN, NOW)
        self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "vecino", "abc", PIN, NOW)
        client = WebClient(self.app)
        status, headers, _ = client.login(101, PIN)
        self.assertEqual(status, 303)
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Lax", headers["Set-Cookie"])
        status, _, html = client.get("/cuenta")
        self.assertEqual(status, 200)
        self.assertIn("Ana Torres", html)

    # AA-04
    def test_aa04_lock_after_five_failures(self):
        for _ in range(5):
            self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "vecino", "101", "000001", NOW)
        self.assertRule("ACCOUNT_LOCKED", authenticate, self.store, "vecino", "101", PIN, NOW)
        later = NOW + timedelta(minutes=15, seconds=1)
        self.assertEqual(authenticate(self.store, "vecino", "101", PIN, later), 101)
        self.assertEqual(self.store.credentials[("vecino", "101")].failures, 0)

    # AA-05
    def test_aa05_anonymous_is_redirected(self):
        client = WebClient(self.app)
        status, headers, _ = client.get("/cuenta")
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/entrar")
        self.assertEqual(client.get("/")[0], 200)
        self.assertEqual(client.post("/pedidos", dict(CA01))[0], 303)
        self.assertEqual(self.store.orders, {})

    # AA-06
    def test_aa06_customer_comes_from_session(self):
        client = WebClient(self.app)
        client.login(101, PIN)
        status, _, html = client.post("/pedidos", dict(CA01, cliente="105", metodo="YAPE", codigo="OP-AA6",
                                                        monto="59.51", saldo="0"))
        self.assertEqual(status, 200)
        self.assertEqual(self.store.orders[1].customer_id, 101)

    # AA-07
    def test_aa07_admin_is_protected(self):
        neighbor = WebClient(self.app)
        neighbor.login(101, PIN)
        self.assertEqual(neighbor.get("/admin")[0], 403)
        self.assertEqual(neighbor.post("/admin/liquidar", {"ciclo": "2026-W38"})[0], 403)
        admin = WebClient(self.app)
        self.assertEqual(admin.login("admin-yapa", ADMIN_PASS, kind="admin")[0], 303)
        self.assertEqual(admin.get("/admin")[0], 200)
        self.assertRule("INVALID_PASSWORD", set_admin_password, self.store, "admin-2", "corta")

    # AA-08
    def test_aa08_csrf_required(self):
        client = WebClient(self.app)
        client.login(101, PIN)
        status, _, _ = client.post("/pedidos", dict(CA01, metodo="YAPE", codigo="OP-AA8", monto="59.51", saldo="0"),
                                   with_csrf=False)
        self.assertEqual(status, 403)
        self.assertEqual(self.store.orders, {})
        client.csrf = "falso"
        self.assertEqual(client.post("/pedidos", dict(CA01, metodo="YAPE", codigo="OP-AA8", monto="59.51"))[0], 403)

    # AA-09
    def test_aa09_logout(self):
        client = WebClient(self.app)
        client.login(101, PIN)
        old_cookie = client.cookie
        self.assertEqual(client.post("/salir")[0], 303)
        client.cookie = old_cookie
        status, headers, _ = client.get("/cuenta")
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/entrar")

    # AA-11 · el valor real de producción (S-67), aunque las pruebas lo bajen por velocidad
    def test_aa11_production_iterations(self):
        import importlib
        from yapa_sdd import auth
        fresh = importlib.reload(auth)
        self.assertEqual(fresh.ITERATIONS, 200_000)

    # AA-10
    def test_aa10_change_pin(self):
        change_pin(self.store, 101, PIN, "907316", NOW)
        self.assertEqual(authenticate(self.store, "vecino", "101", "907316", NOW), 101)
        self.assertRule("INVALID_CREDENTIALS", change_pin, self.store, 101, "000001", "551982", NOW)
        client = WebClient(self.app)
        client.login(101, "907316")
        status, _, _ = client.post("/cuenta/pin", {"actual": "907316", "nuevo": "551982"})
        self.assertEqual(status, 200)
        self.assertEqual(authenticate(self.store, "vecino", "101", "551982", NOW), 101)


if __name__ == "__main__":
    unittest.main()
