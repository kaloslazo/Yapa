"""Iteración 39: "Olvidé mi PIN" sin bot (docs/desarrollo/39-fotos-huerfanas-pin.md)."""

from dataclasses import replace
import unittest

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, PIN, WEDNESDAY
from web_client import fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.domain import Customer
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api


class ForgottenPinTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        self.store.customers[101] = replace(self.store.customers[101], phone="987654321")
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.api = create_api(self.store, clock=lambda: WEDNESDAY)

    def ask(self, user):
        return ApiClient(self.api).post("/api/pin/olvide", {"usuario": user}, with_csrf=False)

    def admin(self):
        client = ApiClient(self.api)
        client.login(ADMIN, ADMIN_PASS, "admin")
        return client

    def open_requests(self):
        status, body, _ = self.admin().get("/api/admin/pin-solicitudes")
        self.assertEqual(status, 200, body)
        return body["solicitudes"]

    # OP-A
    def test_op_a_misma_respuesta_exista_o_no(self):
        known = self.ask("101")
        unknown = self.ask("987654")
        self.assertEqual(known[0], 200)
        self.assertEqual((known[0], known[1]), (unknown[0], unknown[1]))

    # OP-B
    def test_op_b_se_crea_y_el_admin_la_ve(self):
        self.ask("101")
        [request] = self.open_requests()
        self.assertEqual((request["cliente"], request["vecino"], request["celular"]), (101, "Ana Torres", "987654321"))

    # OP-C
    def test_op_c_no_se_duplica(self):
        self.ask("101")
        self.ask("101")
        self.assertEqual(len(self.open_requests()), 1)

    # OP-D
    def test_op_d_tope_de_solicitudes_abiertas(self):
        for customer_id in range(1001, 1101):
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", "Z-LINCE-01"))
            self.ask(str(customer_id))
        self.assertEqual(len(self.open_requests()), 100)
        before = self.ask("101")
        self.assertEqual(before[0], 200)
        self.assertEqual(len(self.open_requests()), 100)
        self.assertEqual(before[1], self.ask("987654")[1])

    # OP-E
    def test_op_e_formato(self):
        for bad in ("", "abc", " "):
            status, body, _ = self.ask(bad)
            self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_INPUT"))

    # OP-F
    def test_op_f_solo_admin(self):
        status, body, _ = ApiClient(self.api).get("/api/admin/pin-solicitudes")
        self.assertEqual((status, body["error"]["codigo"]), (401, "LOGIN_REQUIRED"))
        neighbor = ApiClient(self.api)
        neighbor.login(101, PIN, "vecino")
        status, body, _ = neighbor.get("/api/admin/pin-solicitudes")
        self.assertEqual((status, body["error"]["codigo"]), (403, "FORBIDDEN"))

    # OP-G
    def test_op_g_un_pin_nuevo_cierra_la_solicitud(self):
        self.ask("101")
        status, body, _ = self.admin().post("/api/admin/vecinos/101/pin")
        self.assertEqual(status, 200, body)
        self.assertEqual(self.open_requests(), [])
        client = ApiClient(self.api)
        self.assertEqual(client.post("/api/sesion", {"tipo": "vecino", "usuario": "101", "secreto": body["pin"]},
                                     with_csrf=False)[0], 200)

    # OP-H
    def test_op_h_descartar_no_cambia_el_pin(self):
        self.ask("101")
        [request] = self.open_requests()
        status, _, _ = self.admin().post(f"/api/admin/pin-solicitudes/{request['id']}/descartar")
        self.assertEqual(status, 200)
        self.assertEqual(self.open_requests(), [])
        status, _, _ = ApiClient(self.api).post("/api/sesion", {"tipo": "vecino", "usuario": "101", "secreto": PIN}, with_csrf=False)
        self.assertEqual(status, 200)

    # OP-I
    def test_op_i_descartar_inexistente(self):
        status, body, _ = self.admin().post("/api/admin/pin-solicitudes/999/descartar")
        self.assertEqual((status, body["error"]["codigo"]), (422, "PIN_REQUEST_NOT_FOUND"))

    # OP-J
    def test_op_j_ninguna_respuesta_lleva_el_pin(self):
        self.ask("101")
        texts = [str(self.ask("101")[1]), str(self.open_requests())]
        for text in texts:
            self.assertNotIn(PIN, text)


if __name__ == "__main__":
    unittest.main()
