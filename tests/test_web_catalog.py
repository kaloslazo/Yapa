"""Criterios de la iteración 20 (docs/desarrollo/20-catalogo-web.md)."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.app import create_app


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
MONDAY = datetime(2026, 9, 21, 10, 0, tzinfo=LIMA)
TUESDAY = datetime(2026, 9, 22, 10, 0, tzinfo=LIMA)
W38, W39 = "2026-W38", "2026-W39"
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
HEADER = "codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1,desde2,precio2"
PAPA = "PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,300,SUP-FRESCOS,0,3.50,100,3.30"
LIMPIATODO = "LIMPIATODO-GALON,Limpiatodo galón 3.8 L,LIMPIEZA,unidad,1,60,SUP-LIMPIEZA,0,7.90,12,6.90"
LIST = "\n".join([HEADER, PAPA, LIMPIATODO])


class WebCatalogTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.app = create_app(self.store, clock=lambda: self.now)
        self.at(SATURDAY)

    def at(self, moment):
        self.now = moment
        self.admin = WebClient(self.app)
        self.admin.login(ADMIN, ADMIN_PASS, kind="admin")

    def publish(self, text, cycle=W39):
        return self.admin.post("/admin/catalogo", {"ciclo": cycle, "lista": text})

    def assertRejected(self, response, code):
        status, _, html = response
        self.assertEqual(status, 422)
        self.assertIn(code, html)
        return html

    # CW-A
    def test_cw_a_page_prefills_next_cycle_with_base_catalog(self):
        status, _, html = self.admin.get("/admin/catalogo")
        self.assertEqual(status, 200)
        self.assertIn(W39, html)
        self.assertIn("catálogo base", html)
        self.assertIn("PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,400,SUP-FRESCOS,0,3.60,100,3.38,250,3.20", html)
        self.assertNotIn("PLATANO-SEDA,", html)

    def test_cw01_invalid_cycle_in_query(self):
        self.assertRejected(self.admin.get("/admin/catalogo?ciclo=2026-W99"), "INVALID_CYCLE")

    # CW-B
    def test_cw_b_publish_from_web(self):
        status, _, _ = self.publish(LIST)
        self.assertEqual(status, 200)
        catalog = self.store.catalogs[W39]
        self.assertEqual(set(catalog), {"PAPA-AMARILLA", "LIMPIATODO-GALON"})
        self.assertEqual(catalog["PAPA-AMARILLA"].max_available, D("300"))
        self.assertEqual(catalog["LIMPIATODO-GALON"].name, "Limpiatodo galón 3.8 L")
        self.at(MONDAY)
        html = WebClient(self.app).get("/")[2]
        self.assertIn("S/ 3.92", html)
        self.assertNotIn("S/ 4.03", html)

    def test_cw_b_page_shows_published_catalog(self):
        self.publish(LIST)
        html = self.admin.get(f"/admin/catalogo?ciclo={W39}")[2]
        self.assertIn("publicado", html)
        self.assertIn(PAPA, html)
        self.assertNotIn("PAPA-BLANCA,", html)

    # CW-C
    def test_cw_c_comma_decimal_rejects_whole_list(self):
        html = self.assertRejected(self.publish("\n".join([HEADER, PAPA.replace("3.50", "3,50"), LIMPIATODO])),
                                   "INVALID_CATALOG_FORMAT")
        self.assertIn("línea 2", html)
        self.assertNotIn(W39, self.store.catalogs)

    def test_cw_c_short_line_rejected(self):
        html = self.assertRejected(self.publish("\n".join([PAPA, "AJO,Ajo,FRESCOS,kg,0.25,40,SUP-FRESCOS,0"])),
                                   "INVALID_CATALOG_FORMAT")
        self.assertIn("línea 2", html)
        self.assertNotIn(W39, self.store.catalogs)

    def test_cw02_odd_tiers_and_missing_name_rejected(self):
        self.assertRejected(self.publish(PAPA + ",250"), "INVALID_CATALOG_FORMAT")
        self.assertRejected(self.publish(PAPA.replace("Papa amarilla", " ")), "INVALID_CATALOG_FORMAT")
        self.assertRejected(self.publish(""), "INVALID_CATALOG_FORMAT")
        self.assertNotIn(W39, self.store.catalogs)

    # CW-D
    def test_cw_d_rising_tier_rejected_by_catalog_rule(self):
        self.assertRejected(self.publish("\n".join([LIMPIATODO, PAPA.replace("3.30", "3.70")])), "INVALID_TIERS")
        self.assertNotIn(W39, self.store.catalogs)

    # CW-E
    def test_cw_e_open_cycle_is_locked(self):
        self.at(TUESDAY)
        self.assertRejected(self.publish(LIST), "CATALOG_LOCKED")

    # CW-F
    def test_cw_f_deactivate_from_web(self):
        self.publish(LIST)
        self.at(TUESDAY)
        status, _, _ = self.admin.post("/admin/catalogo/desactivar", {"ciclo": W39, "producto": "PAPA-AMARILLA"})
        self.assertEqual(status, 200)
        self.assertFalse(self.store.catalogs[W39]["PAPA-AMARILLA"].active)
        html = WebClient(self.app).get("/")[2]
        self.assertNotIn("Papa amarilla", html)
        self.assertIn("Limpiatodo", html)

    def test_cw04_unknown_product(self):
        self.assertRejected(self.admin.post("/admin/catalogo/desactivar", {"ciclo": W39, "producto": "MANDARINA"}),
                            "PRODUCT_NOT_AVAILABLE")

    # CW-G
    def test_cw_g_deactivate_copies_base_catalog(self):
        self.at(WEDNESDAY)
        status, _, _ = self.admin.post("/admin/catalogo/desactivar", {"ciclo": W38, "producto": "AJO"})
        self.assertEqual(status, 200)
        self.assertFalse(self.store.catalogs[W38]["AJO"].active)
        self.assertEqual(set(self.store.catalogs[W38]), set(self.store.products))
        self.assertTrue(self.store.catalogs[W38]["PAPA-AMARILLA"].active)
        self.assertTrue(self.store.products["AJO"].active)

    # CW-I
    def test_cw_i_zero_step_rejected(self):
        self.assertRejected(self.publish(PAPA.replace(",kg,1,", ",kg,0,")), "INVALID_STOCK")
        self.assertNotIn(W39, self.store.catalogs)

    # CW-H
    def test_cw_h_neighbor_forbidden(self):
        neighbor = WebClient(self.app)
        neighbor.login(101, PIN)
        self.assertEqual(neighbor.get("/admin/catalogo")[0], 403)
        self.assertEqual(neighbor.post("/admin/catalogo", {"ciclo": W39, "lista": LIST})[0], 403)
        self.assertNotIn(W39, self.store.catalogs)


if __name__ == "__main__":
    unittest.main()
