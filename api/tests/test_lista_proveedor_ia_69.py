"""Iteración 69 · La cotización del proveedor leída con IA. Spec: docs/desarrollo/69-lista-del-proveedor-con-ia.md.
Ninguna prueba sale a internet: el envío HTTP se reemplaza por un proveedor falso (como en test_ia)."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_ia import Falso
from web_client import fast_hashing

from yapa_sdd import ia, partners, quote_reader
from yapa_sdd.auth import set_admin_password
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

NOW = datetime(2026, 11, 14, 10, 0, tzinfo=LIMA)
SUPPLIER, PASS = "frescos", "frescos-2026"
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64
PHOTO = ("lista.jpg", JPEG)
TEXT = "Papa amarilla .... S/ 3.40 kg (hay 300 kg)\n   desde 100 kg a 3.10\nCebolla roja S/ 1.90\nAlgo que no vendo S/ 9"
AI_ROWS = {"filas": [
    {"codigo": "PAPA-AMARILLA", "nombre": "Papa amarilla", "unidad": "kg", "maximo": 300,
     "tramos": [{"desde": 100, "precio": 3.1}, {"desde": 0, "precio": 3.4}]},
    {"codigo": "CEBOLLA-ROJA", "nombre": "Cebolla roja", "unidad": "kg", "maximo": None, "tramos": [{"desde": 0, "precio": 1.9}]},
    {"codigo": "", "nombre": "Papa huayro", "unidad": "kg", "maximo": None, "tramos": [{"desde": 0, "precio": 4.2}]},
    {"codigo": "LEJIA-GALON", "nombre": "Lejía", "unidad": "unidad", "maximo": 10, "tramos": [{"desde": 0, "precio": 9}]},
    {"codigo": "LIMON", "nombre": "Limón", "unidad": "kg", "maximo": 80, "tramos": [{"desde": 0, "precio": 0}]},
]}


def row(result: dict, code: str) -> dict:
    return next(r for r in result["filas"] if r["codigo"] == code)


class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.store = pilot_store()
        partners.create_supplier_account(self.store, SUPPLIER, "SUP-FRESCOS", PASS, by="admin-yapa", now=NOW)

    def read(self, ai=None, text="", photo=None):
        return quote_reader.read_quote(self.store, ai, SUPPLIER, text=text, photo=photo, now=NOW)

    def client(self, **answers):
        fake = Falso(**answers)
        return ia.AIClient([ia.Provider("groq", ia.GROQ_URL, "k", "texto", "vision")], post=fake), fake

    def assertRule(self, code, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            self.read(*args, **kwargs)
        self.assertEqual(raised.exception.code, code)

    # LP-A
    def test_lp_a_photo_with_ai_fills_known_and_new_products(self):
        ai, _ = self.client(groq=AI_ROWS)
        result = self.read(ai, photo=PHOTO)
        self.assertEqual(result["fuente"], "ia")
        papa = row(result, "PAPA-AMARILLA")
        self.assertEqual((papa["categoria"], papa["unidad"], papa["paso"], papa["maximo"]), ("FRESCOS", "kg", D("1"), D("300")))
        self.assertEqual(papa["tramos"], [{"desde": D("0"), "precio": D("3.4")}, {"desde": D("100"), "precio": D("3.1")}])
        huayro = row(result, "PAPA-HUAYRO")
        self.assertEqual((huayro["categoria"], huayro["paso"], huayro["maximo"]), ("FRESCOS", D("1"), D("0")))
        self.assertEqual(result["nuevos"], ["PAPA-HUAYRO"])

    # LP-B
    def test_lp_b_foreign_codes_and_bad_prices_are_dropped_with_a_warning(self):
        ai, _ = self.client(groq=AI_ROWS)
        result = self.read(ai, photo=PHOTO)
        codes = [r["codigo"] for r in result["filas"]]
        self.assertNotIn("LEJIA-GALON", codes)
        self.assertNotIn("LIMON", codes)
        self.assertEqual(len(result["avisos"]), 2)

    # LP-C
    def test_lp_c_missing_quantity_keeps_the_current_maximum(self):
        ai, _ = self.client(groq=AI_ROWS)
        self.assertEqual(row(self.read(ai, photo=PHOTO), "CEBOLLA-ROJA")["maximo"], D("300"))

    # LP-D
    def test_lp_d_text_without_ai_is_read_with_rules(self):
        result = self.read(text=TEXT)
        self.assertEqual(result["fuente"], "reglas")
        papa = row(result, "PAPA-AMARILLA")
        self.assertEqual(papa["maximo"], D("300"))
        self.assertEqual(papa["tramos"], [{"desde": D("0"), "precio": D("3.40")}, {"desde": D("100"), "precio": D("3.10")}])
        self.assertEqual(row(result, "CEBOLLA-ROJA")["tramos"][0]["precio"], D("1.90"))
        self.assertEqual(len(result["filas"]), 2)

    # LP-E
    def test_lp_e_ai_down_with_text_falls_back_to_rules(self):
        ai, _ = self.client(groq=ia.AIError("caído"))
        result = self.read(ai, text=TEXT)
        self.assertEqual(result["fuente"], "reglas")
        self.assertTrue(result["avisos"])

    # LP-F
    def test_lp_f_photo_needs_ai(self):
        self.assertRule("IA_DISABLED", photo=PHOTO)
        ai, _ = self.client(groq=ia.AIError("caído"))
        self.assertRule("IA_UNAVAILABLE", ai, photo=PHOTO)

    # LP-G
    def test_lp_g_empty_and_invalid_photo(self):
        self.assertRule("LIST_REQUIRED", text="   ")
        ai, _ = self.client(groq=AI_ROWS)
        self.assertRule("INVALID_PHOTO", ai, photo=("lista.txt", b"hola"))

    # LP-H
    def test_lp_h_daily_limit(self):
        for _ in range(20):
            self.read(text=TEXT)
        self.assertRule("IA_LIMIT", text=TEXT)

    # LP-I
    def test_lp_i_the_photo_goes_to_the_vision_model(self):
        ai, fake = self.client(groq=AI_ROWS)
        self.read(ai, photo=PHOTO)
        body = fake.enviados[0]
        self.assertEqual(body["model"], "vision")
        image = body["messages"][1]["content"][1]
        self.assertEqual(image["type"], "image_url")
        self.assertTrue(image["image_url"]["url"].startswith("data:image/jpeg;base64,"))


class ReaderApiTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        partners.create_supplier_account(self.store, SUPPLIER, "SUP-FRESCOS", PASS, by="admin-yapa", now=NOW)
        set_admin_password(self.store, "admin-yapa", "yapa-admin-2026")
        self.api = create_api(self.store, clock=lambda: NOW, security_clock=lambda: NOW)

    # LP-01
    def test_lp_01_supplier_reads_a_text_list(self):
        supplier = ApiClient(self.api)
        self.assertEqual(supplier.login(SUPPLIER, PASS, "proveedor")[0], 200)
        status, data, _ = supplier.post("/api/proveedor/lista/leer", {"texto": TEXT})
        self.assertEqual(status, 200)
        papa = next(r for r in data["filas"] if r["codigo"] == "PAPA-AMARILLA")
        self.assertEqual(papa["tramos"][1], {"desde": "100", "precio": "3.10"})
        self.assertEqual(data["fuente"], "reglas")

    # LP-J
    def test_lp_j_admin_cannot_read_a_supplier_list(self):
        admin = ApiClient(self.api)
        self.assertEqual(admin.login("admin-yapa", "yapa-admin-2026", "admin")[0], 200)
        self.assertEqual(admin.post("/api/proveedor/lista/leer", {"texto": TEXT})[0], 403)


if __name__ == "__main__":
    unittest.main()
