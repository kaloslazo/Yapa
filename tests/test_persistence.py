import os
import sqlite3
import tempfile
from datetime import datetime
from decimal import Decimal
import unittest

from test_catalog import ADMIN, SATURDAY, W39, w39_catalog
from test_settlement import CYCLE, Scenario
from web_client import WebClient, fast_hashing

from yapa_sdd import persistence
from yapa_sdd.auth import authenticate, set_admin_password, set_pin
from yapa_sdd.catalog import publish_catalog
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError, Customer
from yapa_sdd.order_registration import quote_order, register_order
from yapa_sdd.seed import pilot_store
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.wallet import request_withdrawal
from yapa_sdd.web.app import create_app
from yapa_sdd.zones import create_zone


NOW = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
LINES = [("PAPA-AMARILLA", "5"), ("LIMPIATODO-GALON", "4")]


def state(store):
    return {key: value for key, value in vars(store).items()}


class PersistenceSpecTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        folder = tempfile.mkdtemp()
        self.path = os.path.join(folder, "yapa.db")

    def rich_store(self):
        s = Scenario()
        s.orders("Z-JM-01", 20)
        settle_cycle(s.store, CYCLE, at=NOW)
        first = s.store.orders[1].customer_id
        request_withdrawal(s.store, first, Decimal("5"), NOW)
        s.store.add_customer(Customer(9001, "Admin de zona", "Z-LINCE-01", lat=-12.085, lon=-77.035))
        create_zone(s.store, 9001, name="Edificio Los Pinos", district="Lince", lat=-12.085, lon=-77.035, now=NOW)
        publish_catalog(s.store, W39, w39_catalog(), by=ADMIN, now=SATURDAY)
        set_pin(s.store, 101, "482915")
        return s.store

    # PA-01
    def test_pa01_roundtrip_pilot(self):
        store = pilot_store()
        persistence.save(store, self.path)
        self.assertEqual(state(persistence.load(self.path)), state(store))

    # PA-02
    def test_pa02_roundtrip_everything(self):
        store = self.rich_store()
        persistence.save(store, self.path)
        loaded = persistence.load(self.path)
        for key, value in state(store).items():
            with self.subTest(part=key):
                self.assertEqual(getattr(loaded, key), value)
        self.assertIsInstance(loaded.orders[1].total, Decimal)
        self.assertIsNotNone(loaded.orders[1].payments[0].status)
        self.assertEqual(loaded.settlements[CYCLE].orders[1].final_amount, Decimal("48.14"))

    # PA-03
    def test_pa03_continuity_after_load(self):
        store = self.rich_store()
        persistence.save(store, self.path)
        loaded = persistence.load(self.path)
        order = register_order(loaded, customer_id=101, lines=LINES, payment_method="YAPE", operation_code="NUEVO-1",
                               amount=quote_order(loaded, LINES).total, now=NOW)
        self.assertEqual(order.order_id, 21)
        with self.assertRaises(BusinessRuleError) as raised:
            register_order(loaded, customer_id=105, lines=LINES, payment_method="YAPE", operation_code="OP1001",
                           amount=quote_order(loaded, LINES).total, now=NOW)
        self.assertEqual(raised.exception.code, "PAYMENT_CODE_ALREADY_USED")
        self.assertEqual(authenticate(loaded, "vecino", "101", "482915", NOW), 101)

    # PA-04
    def test_pa04_save_is_all_or_nothing(self):
        store = pilot_store()
        persistence.save(store, self.path)
        store.add_customer(Customer(4242, "Nuevo", "Z-LINCE-01"))  # 'customers' se escribe primero...
        store.used_codes.add("FALLA")  # ...y la falla llega después, al guardar los códigos usados
        original = persistence._encode

        def broken(value):
            if isinstance(value, set) and "FALLA" in value:
                raise RuntimeError("falla simulada a mitad del guardado")
            return original(value)

        persistence._encode = broken
        self.addCleanup(setattr, persistence, "_encode", original)
        with self.assertRaises(RuntimeError):
            persistence.save(store, self.path)
        persistence._encode = original
        self.assertNotIn(4242, persistence.load(self.path).customers)
        self.assertIn(101, persistence.load(self.path).customers)

    # PA-05
    def test_pa05_tampered_database_is_rejected(self):
        persistence.save(pilot_store(), self.path)
        with sqlite3.connect(self.path) as conn:
            conn.execute("UPDATE estado SET valor = ? WHERE clave = 'admins'",
                         ('{"$dc": "subprocess.Popen", "f": {"args": "calc"}}',))
        with self.assertRaises(BusinessRuleError) as raised:
            persistence.load(self.path)
        self.assertEqual(raised.exception.code, "PERSISTENCE_INVALID_DATA")

    # PA-06
    def test_pa06_web_saves_after_successful_posts_only(self):
        store = pilot_store()
        set_pin(store, 101, "482915")
        persistence.save(store, self.path)
        app = create_app(store, clock=lambda: NOW, on_change=lambda s: persistence.save(s, self.path))
        web = WebClient(app)
        web.login(101, "482915")
        status, _, _ = web.post("/pedidos", {"cant_PAPA-AMARILLA": "5", "cant_LIMPIATODO-GALON": "4",
                                             "metodo": "YAPE", "codigo": "WEB-P1", "monto": "59.60", "saldo": "0"})
        self.assertEqual(status, 200)
        self.assertIn(1, persistence.load(self.path).orders)
        before = os.path.getmtime(self.path), persistence.load(self.path).orders.keys()
        status, _, _ = web.post("/pedidos", {"cant_PAPA-AMARILLA": "5", "metodo": "YAPE", "codigo": "WEB-P2",
                                             "monto": "20", "saldo": "0"})
        self.assertEqual(status, 422)
        self.assertEqual(persistence.load(self.path).orders.keys(), before[1])

    # PA-07
    def test_pa07_open_store_creates_or_loads(self):
        store = persistence.open_store(self.path)
        self.assertTrue(os.path.exists(self.path))
        self.assertIn(101, store.customers)
        store.add_customer(Customer(5151, "Guardado", "Z-LINCE-01"))
        persistence.save(store, self.path)
        self.assertIn(5151, persistence.open_store(self.path).customers)


if __name__ == "__main__":
    unittest.main()
