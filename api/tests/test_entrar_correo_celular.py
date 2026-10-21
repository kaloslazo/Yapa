"""Iteración 46 · Entrar con correo o celular. Spec: docs/desarrollo/46-entrar-con-correo-o-celular.md."""

import unittest
from dataclasses import replace
from datetime import datetime, timedelta

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, PIN, WEDNESDAY
from test_cuenta_correo import FakeMailer
from web_client import fast_hashing

from yapa_sdd.auth import MAX_FAILURES, set_admin_password, set_pin
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

PHONE, EMAIL = "987654321", "ana.torres@gmail.com"
OTHER_PIN = "246802"
NEW_PIN = "739104"


class LoginBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        now = datetime(2026, 9, 1, tzinfo=WEDNESDAY.tzinfo)
        self.store.customers[101] = replace(self.store.customers[101], phone=PHONE, email=EMAIL, email_verified_at=now)
        self.store.customers[104] = replace(self.store.customers[104], phone="911222333", email="jorge@gmail.com")
        self.store.customers[105] = replace(self.store.customers[105], phone="922333444", email="carmen@gmail.com",
                                            email_verified_at=now)  # sin PIN: nació con Google
        set_pin(self.store, 101, PIN)
        set_pin(self.store, 104, OTHER_PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.clock = [WEDNESDAY]
        self.mailer = FakeMailer()
        self.api = create_api(self.store, clock=lambda: self.clock[0], mailer=self.mailer, background_mail=False)

    def enter(self, user, secret, kind="vecino"):
        client = ApiClient(self.api)
        status, body, _ = client.login(user, secret, kind)
        return client, status, body

    def code_of(self, body):
        return body["error"]["codigo"]


class EnterTests(LoginBase):
    # LG-A
    def test_lg_a_con_el_correo(self):
        for text in (EMAIL, EMAIL.upper(), f"  {EMAIL}  "):
            _, status, body = self.enter(text, PIN)
            self.assertEqual((status, body["usuario"]), (200, 101), text)

    # LG-B
    def test_lg_b_con_el_celular(self):
        _, status, body = self.enter(PHONE, PIN)
        self.assertEqual((status, body["usuario"]), (200, 101))

    # LG-C, LG-07
    def test_lg_c_con_el_numero(self):
        _, status, body = self.enter("101", PIN)
        self.assertEqual((status, body["usuario"]), (200, 101))

    # LG-D
    def test_lg_d_quien_no_existe_da_el_mismo_error(self):
        errors = []
        for user in ("nadie@gmail.com", "933000111", "999", "101"):
            _, status, body = self.enter(user, "000000" if user == "101" else PIN)
            errors.append((status, self.code_of(body), body["error"]["mensaje"]))
        self.assertEqual(len(set(errors)), 1, errors)
        self.assertEqual(errors[0][:2], (422, "INVALID_CREDENTIALS"))

    # LG-E
    def test_lg_e_pin_de_otra_persona(self):
        _, status, body = self.enter(EMAIL, OTHER_PIN)
        self.assertEqual((status, self.code_of(body)), (422, "INVALID_CREDENTIALS"))

    # LG-F
    def test_lg_f_los_fallos_por_correo_bloquean_la_cuenta(self):
        for _ in range(MAX_FAILURES):
            self.enter(EMAIL, "000000")
        _, status, body = self.enter("101", PIN)
        self.assertEqual((status, self.code_of(body)), (422, "ACCOUNT_LOCKED"))

    # LG-M
    def test_lg_m_el_admin_sigue_con_su_usuario(self):
        _, status, body = self.enter(ADMIN, ADMIN_PASS, "admin")
        self.assertEqual((status, body["rol"]), (200, "admin"))
        _, status, body = self.enter(EMAIL, ADMIN_PASS, "admin")
        self.assertEqual((status, self.code_of(body)), (422, "INVALID_CREDENTIALS"))
        set_admin_password(self.store, "101", ADMIN_PASS)  # un admin con el mismo texto que el número de Ana
        for text in (EMAIL, PHONE):
            _, status, body = self.enter(text, ADMIN_PASS, "admin")
            self.assertEqual((status, self.code_of(body)), (422, "INVALID_CREDENTIALS"), text)

    # LG-L, LG-06
    def test_lg_l_tiene_pin(self):
        client, _, body = self.enter(EMAIL, PIN)
        self.assertTrue(body["tiene_pin"])
        self.assertTrue(client.get("/api/sesion")[1]["tiene_pin"])
        self.assertFalse(self.google_session(105).get("/api/sesion")[1]["tiene_pin"])

    def google_session(self, customer_id):
        """Una sesión de quien no tiene PIN (como si hubiera entrado con Google)."""
        client = ApiClient(self.api)
        set_pin(self.store, customer_id, NEW_PIN)
        client.login(customer_id, NEW_PIN)
        del self.store.credentials[("vecino", str(customer_id))]
        return client


class RecoveryTests(LoginBase):
    # LG-G
    def test_lg_g_olvide_con_el_correo(self):
        status, body, _ = ApiClient(self.api).post("/api/pin/olvide", {"usuario": EMAIL.upper()}, with_csrf=False)
        self.assertEqual(status, 200)
        self.assertEqual(self.mailer.sent[-1][0], EMAIL)
        self.assertIn("Si tu número está registrado", body["mensaje"])
        sent = len(self.mailer.sent)
        status2, body2, _ = ApiClient(self.api).post("/api/pin/olvide", {"usuario": "nadie@gmail.com"}, with_csrf=False)
        self.assertEqual((status2, body2), (status, body))
        self.assertEqual(len(self.mailer.sent), sent)

    # LG-H
    def test_lg_h_restablecer_con_el_celular(self):
        ApiClient(self.api).post("/api/pin/olvide", {"usuario": PHONE}, with_csrf=False)
        code = self.mailer.last_code()
        status, body, _ = ApiClient(self.api).post("/api/pin/restablecer", {"usuario": PHONE, "codigo": code, "pin": NEW_PIN}, with_csrf=False)
        self.assertEqual(status, 200, body)
        self.assertEqual(self.enter(EMAIL, NEW_PIN)[1], 200)
        self.assertEqual(self.enter(PHONE, PIN)[1], 422)


class CreatePinTests(LoginBase):
    def google_neighbor(self):
        return EnterTests.google_session(self, 105)

    # LG-I
    def test_lg_i_crear_pin(self):
        client = self.google_neighbor()
        status, body, _ = client.post("/api/pin/crear", {"pin": NEW_PIN})
        self.assertEqual(status, 200, body)
        _, status, body = self.enter("carmen@gmail.com", NEW_PIN)
        self.assertEqual((status, body["usuario"], body["tiene_pin"]), (200, 105, True))

    # LG-J
    def test_lg_j_quien_ya_tiene_pin_no_lo_crea_de_nuevo(self):
        client, _, _ = self.enter("101", PIN)
        status, body, _ = client.post("/api/pin/crear", {"pin": NEW_PIN})
        self.assertEqual((status, self.code_of(body)), (422, "PIN_ALREADY_SET"))
        self.assertEqual(self.enter("101", PIN)[1], 200)
        self.assertEqual(self.enter("101", NEW_PIN)[1], 422)

    # LG-K
    def test_lg_k_pin_flojo(self):
        client = self.google_neighbor()
        for weak in ("123456", "111111", "12345", ""):
            status, body, _ = client.post("/api/pin/crear", {"pin": weak})
            self.assertEqual((status, self.code_of(body)), (422, "INVALID_PIN"), weak)
        self.assertNotIn(("vecino", "105"), self.store.credentials)

    def test_lg_i_solo_con_sesion_de_vecino(self):
        self.assertEqual(ApiClient(self.api).post("/api/pin/crear", {"pin": NEW_PIN}, with_csrf=False)[0], 401)
        admin, _, _ = self.enter(ADMIN, ADMIN_PASS, "admin")
        self.assertEqual(admin.post("/api/pin/crear", {"pin": NEW_PIN})[0], 403)


if __name__ == "__main__":
    unittest.main()
