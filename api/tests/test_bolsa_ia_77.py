"""Iteración 77 · Revisar la bolsa con IA que conoce el pedido. Spec: docs/desarrollo/77-revision-de-bolsas-con-ia.md.

Ninguna prueba sale a internet: la IA es el proveedor falso de test_ia y el detector local (YOLO) se reemplaza.
"""
import json
import unittest
from unittest.mock import patch

from api_client import ApiClient
from test_ia import Falso, cliente
from test_settlement import NOW, Scenario
from web_client import fast_hashing

from yapa_sdd import cycle as cycles, ia, partners, vision
from yapa_sdd.auth import set_admin_password
from yapa_sdd.web.api import create_api

ADMIN, ADMIN_PASS, PASS = "admin-yapa", "yapa-admin-2026", "clave-prueba-2026"
PACKER, SUPPLIER = "armado-77", "frescos-77"
PHOTO = ("bolsa.jpg", b"\xff\xd8\xff\xe0" + b"0" * 64)
DETECTOR = {"modelo": "Yapa YOLOv8 Small", "umbral": 0.35,
            "productos": [{"producto": "papa", "cantidad": 2, "confianza": 0.8}], "aviso": "Sugerencia."}
DOWN = ia.AIError("caído")


class BagReaderTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.order = self.s.order("Z-JM-01")  # papa amarilla, papa blanca y cebolla roja
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        partners.create_staff(self.store, PACKER, partners.PACKER, "Rosa Armado", PASS, by=ADMIN, now=NOW)
        partners.create_supplier_account(self.store, SUPPLIER, "SUP-FRESCOS", PASS, by=ADMIN, now=NOW)

    def ask(self, falso, data, user=PACKER, kind=partners.PACKER, ai=True):
        app = create_api(self.store, clock=lambda: NOW, ai=cliente(falso) if ai else None)
        client = ApiClient(app)
        self.assertEqual(client.login(user, PASS, kind)[0], 200)
        with patch.object(vision, "analyze_photo", return_value=DETECTOR) as detector:
            status, body = client.post_file("/api/vision/analizar", data, {"foto_archivo": PHOTO})
        return status, body, detector

    def for_order(self):
        return {"pedido": str(self.order.order_id)}

    # VB-A
    def test_vb_a_ai_answers_with_codes_of_the_order(self):
        falso = Falso(groq={"productos": [{"id": "PAPA-BLANCA", "unidades": 3}, {"id": "CEBOLLA-ROJA", "unidades": 2}],
                            "otros": []}, github=DOWN)
        status, body, detector = self.ask(falso, self.for_order())
        self.assertEqual(status, 200)
        self.assertEqual(body["fuente"], "ia")
        self.assertEqual(body["productos"], [
            {"codigo": "PAPA-BLANCA", "nombre": "Papa blanca", "producto": "papa", "cantidad": 3},
            {"codigo": "CEBOLLA-ROJA", "nombre": "Cebolla roja", "producto": "cebolla", "cantidad": 2}])
        detector.assert_not_called()

    # VB-B
    def test_vb_b_only_codes_of_the_order_once(self):
        falso = Falso(groq={"productos": [{"id": "LIMON", "unidades": 2}, {"id": "INVENTADO", "unidades": 1},
                                          {"id": "PAPA-BLANCA", "unidades": 3}, {"id": "PAPA-BLANCA", "unidades": 1}],
                            "otros": ["tomate"]}, github=DOWN)
        _, body, _ = self.ask(falso, self.for_order())
        self.assertEqual([(p["codigo"], p["cantidad"]) for p in body["productos"]], [("PAPA-BLANCA", 3)])
        self.assertEqual(body["otros"], ["tomate"])

    # VB-C
    def test_vb_c_the_ai_gets_the_order_list_and_the_photo_not_the_neighbor(self):
        falso = Falso(groq={"productos": []}, github=DOWN)
        self.ask(falso, self.for_order())
        user = falso.enviados[0]["messages"][1]["content"]
        text = user[0]["text"]
        for code, name in [("PAPA-AMARILLA", "Papa amarilla"), ("PAPA-BLANCA", "Papa blanca"), ("CEBOLLA-ROJA", "Cebolla roja")]:
            self.assertIn(f"{code}: {name}", text)
        self.assertNotIn("LIMON", text)
        self.assertNotIn(self.store.customers[self.order.customer_id].name, json.dumps(falso.enviados[0]))
        self.assertTrue(user[1]["image_url"]["url"].startswith("data:image/jpeg;base64,"))

    # VB-D
    def test_vb_d_without_ai_the_local_detector_answers(self):
        status, body, detector = self.ask(None, self.for_order(), ai=False)
        self.assertEqual(status, 200)
        self.assertEqual(body["fuente"], "detector")
        self.assertEqual(body["productos"], DETECTOR["productos"])
        detector.assert_called_once_with(PHOTO)

    # VB-E
    def test_vb_e_ai_down_falls_back_to_the_detector(self):
        falso = Falso(groq=DOWN, github=DOWN)
        _, body, detector = self.ask(falso, self.for_order())
        self.assertEqual(body["fuente"], "detector")
        detector.assert_called_once()

    # VB-F
    def test_vb_f_after_150_reviews_the_ai_is_not_called(self):
        today = cycles.to_lima(NOW).date().isoformat()
        self.store.ia_usage[f"bolsa:{PACKER}:{today}"] = 150
        falso = Falso(groq={"productos": []}, github=DOWN)
        _, body, _ = self.ask(falso, self.for_order())
        self.assertEqual(falso.enviados, [])
        self.assertEqual(body["fuente"], "detector")

    def test_vb_f_each_ai_review_counts(self):
        falso = Falso(groq={"productos": []}, github=DOWN)
        self.ask(falso, self.for_order())
        today = cycles.to_lima(NOW).date().isoformat()
        self.assertEqual(self.store.ia_usage[f"bolsa:{PACKER}:{today}"], 1)

    # VB-G
    def test_vb_g_the_supplier_list_is_his_own_products(self):
        falso = Falso(groq={"productos": [{"id": "PAPA-AMARILLA", "unidades": 4}, {"id": "LIMPIATODO-GALON", "unidades": 1}]},
                      github=DOWN)
        _, body, _ = self.ask(falso, {"para": "stock"}, user=SUPPLIER, kind=partners.SUPPLIER)
        self.assertEqual([p["codigo"] for p in body["productos"]], ["PAPA-AMARILLA"])
        text = falso.enviados[0]["messages"][1]["content"][0]["text"]
        self.assertIn("PAPA-AMARILLA", text)
        self.assertNotIn("LIMPIATODO-GALON", text)

    # VB-H
    def test_vb_h_unknown_order(self):
        status, body, _ = self.ask(Falso(groq={"productos": []}, github=DOWN), {"pedido": "999999"})
        self.assertEqual(body["error"]["codigo"], "ORDER_NOT_FOUND")

    # VB-I
    def test_vb_i_units_are_pieces_from_1_to_300(self):
        falso = Falso(groq={"productos": [{"id": "PAPA-AMARILLA", "unidades": "muchas"}, {"id": "PAPA-BLANCA", "unidades": 0},
                                          {"id": "CEBOLLA-ROJA", "unidades": 500}]}, github=DOWN)
        _, body, _ = self.ask(falso, self.for_order())
        self.assertEqual([p["cantidad"] for p in body["productos"]], [1, 1, 300])

    # VB-01: sin pedido ni para, igual que antes
    def test_vb_01_without_context_only_the_detector(self):
        falso = Falso(groq={"productos": []}, github=DOWN)
        _, body, detector = self.ask(falso, {})
        self.assertEqual(falso.enviados, [])
        self.assertEqual(body["productos"], DETECTOR["productos"])
        detector.assert_called_once_with(PHOTO)


if __name__ == "__main__":
    unittest.main()
