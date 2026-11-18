"""Iteración 72: stock que el proveedor confirma por cargas. Spec: docs/desarrollo/72-stock-confirmado.md."""
import json
import tempfile
import unittest
from pathlib import Path

from api_client import ApiClient
from test_settlement import NOW, Scenario
from web_client import fast_hashing
from yapa_sdd import partners, persistence, supplier_stock
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.web.api import create_api

NEXT_WEEK = "2026-W39"
FIRST_PHOTO = b"\xff\xd8\xffprimera-foto"


class SupplierStockTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = Scenario().store
        partners.create_supplier_account(self.store, "stock-frescos", "SUP-FRESCOS", "clave-prueba-2026",
                                         by="admin-yapa", now=NOW)
        partners.create_supplier_account(self.store, "stock-limpieza", "SUP-LIMPIEZA", "clave-prueba-2026",
                                         by="admin-yapa", now=NOW)

    def confirm(self, rows, photo=FIRST_PHOTO, user="stock-frescos"):
        return supplier_stock.confirm(self.store, user, NEXT_WEEK, rows, ("foto.jpg", photo), NOW)

    def test_st72_a_rows_add_up_and_the_same_photo_is_not_added_twice(self):
        rows = [{"id": "PAPA-AMARILLA", "unidades": 2, "peso": "1.2"},
                {"id": "PAPA-AMARILLA", "unidades": 3, "peso": "2.3"}]
        first = self.confirm(rows)
        repeat = self.confirm(rows)
        self.assertEqual(first["productos"][0]["cantidad"], "3.5")
        self.assertEqual(repeat["productos"][0]["cantidad"], "3.5")
        self.assertTrue(repeat["repetida"])
        second = self.confirm([{"id": "PAPA-AMARILLA", "unidades": 1, "peso": "0.6"}], b"\xff\xd8\xffsegunda-foto")
        papa = second["productos"][0]
        self.assertEqual((papa["cantidad"], papa["disponible"], papa["unidades"]), ("4.1", "4", 6))

    def test_st72_b_kilos_need_the_measured_weight(self):
        for value in [None, "NaN", "Infinity", "0", "-1"]:
            with self.assertRaises(BusinessRuleError) as e:
                self.confirm([{"id": "ZANAHORIA", "unidades": 3, "peso": value}])
            self.assertEqual(e.exception.code, "WEIGHT_REQUIRED")
        self.assertFalse(self.store.supplier_stock_batches)

    def test_st72_c_another_suppliers_product_saves_nothing(self):
        with self.assertRaises(BusinessRuleError) as e:
            self.confirm([{"id": "AJO", "unidades": 1, "peso": "1"}, {"id": "LIMPIATODO-GALON", "unidades": 1}])
        self.assertEqual(e.exception.code, "INVALID_STOCK_ITEM")
        self.assertFalse(self.store.supplier_stock_batches)

    def test_st72_d_units_stay_units_and_survive_a_restart(self):
        result = self.confirm([{"id": "LIMPIATODO-GALON", "unidades": 3}], user="stock-limpieza")
        self.assertEqual(result["productos"][0]["disponible"], "3")
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "stock.db")
            persistence.save(self.store, path)
            loaded = persistence.load(path)
        self.assertEqual(supplier_stock.snapshot(loaded, "stock-limpieza", NEXT_WEEK)["productos"], result["productos"])

    def test_st72_e_a_confirmed_photo_cannot_change_its_count(self):
        self.confirm([{"id": "AJO", "unidades": 1, "peso": "1"}])
        with self.assertRaises(BusinessRuleError) as e:
            self.confirm([{"id": "AJO", "unidades": 2, "peso": "2"}])
        self.assertEqual(e.exception.code, "STOCK_ALREADY_CONFIRMED")

    def test_st72_f_api_confirms_repeats_and_leaves_the_catalog_alone(self):
        app = create_api(self.store, clock=lambda: NOW)
        client = ApiClient(app)
        self.assertEqual(client.login("stock-frescos", "clave-prueba-2026", "proveedor")[0], 200)
        original = self.store.products["AJO"].max_available
        data = {"ciclo": NEXT_WEEK, "conteo": json.dumps([{"id": "AJO", "unidades": 2, "peso": "0.5"}])}
        photo = {"foto_archivo": ("x.jpg", b"\xff\xd8\xfffoto-api")}
        status, first = client.post_file("/api/proveedor/stock/confirmar", data, photo)
        self.assertEqual(status, 200)
        self.assertEqual(first["productos"][0]["cantidad"], "0.5")
        status, replay = client.post_file("/api/proveedor/stock/confirmar", data, photo)
        self.assertTrue(replay["repetida"])
        self.assertEqual(self.store.products["AJO"].max_available, original)
        self.assertEqual(ApiClient(app).get(f"/api/proveedor/stock?ciclo={NEXT_WEEK}")[0], 401)


if __name__ == "__main__":
    unittest.main()
