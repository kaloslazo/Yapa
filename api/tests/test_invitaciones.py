"""Iteración 45 · Registro por invitación. Spec: docs/desarrollo/45-registro-por-invitacion.md."""

import json
import unittest
from dataclasses import replace
from datetime import timedelta

from api_client import ApiClient
from test_api import PIN, WEDNESDAY
from test_cuenta_correo import FakeMailer
from web_client import fast_hashing

from yapa_sdd.auth import set_pin
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

try:
    from test_google import CLIENT_ID, JWKS, mint
    from yapa_sdd.google_identity import GoogleVerifier
    HAS_GOOGLE = True
except unittest.SkipTest:
    HAS_GOOGLE = False

NEW_PIN = "739104"
DATA = {"nombre": "Lucía Ramos", "celular": "987654321", "correo": "lucia@correo.pe", "consentimiento": True}


class InviteBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        self.now = WEDNESDAY
        self.mailer = FakeMailer()
        google = GoogleVerifier(CLIENT_ID, jwks_provider=lambda: JWKS) if HAS_GOOGLE else None
        self.api = create_api(self.store, clock=lambda: self.now, mailer=self.mailer, google=google, background_mail=False)

    def neighbor(self, customer_id=101, pin=PIN):
        client = ApiClient(self.api)
        client.login(customer_id, pin, "vecino")
        return client

    def my_code(self, customer_id=101, pin=PIN):
        return self.neighbor(customer_id, pin).get("/api/mi-invitacion")[1]["codigo"]

    def public(self):
        return ApiClient(self.api)

    def code_of(self, response):
        return response[1]["error"]["codigo"]

    def start(self, token, **changes):
        return self.public().post(f"/api/invitaciones/{token}/correo", DATA | changes, with_csrf=False)

    def finish(self, token, email="lucia@correo.pe", code=None, pin=NEW_PIN, client=None):
        code = code or self.mailer.last_code()
        return (client or self.public()).post(f"/api/invitaciones/{token}/confirmar",
                                              {"correo": email, "codigo": code, "pin": pin}, with_csrf=False)

    def register(self, token, i=0):
        phone, email = f"9000000{i:02d}", f"vecino{i}@correo.pe"
        started = self.start(token, celular=phone, correo=email, nombre=f"Vecino {i}")
        if started[0] != 200:
            return started
        return self.finish(token, email=email, pin="739104")


class LinkTests(InviteBase):
    # IN-A
    def test_in_a_mi_enlace(self):
        client = self.neighbor()
        first = client.get("/api/mi-invitacion")
        second = client.get("/api/mi-invitacion")
        self.assertEqual(first[0], 200)
        self.assertEqual(first[1]["codigo"], second[1]["codigo"])
        self.assertGreaterEqual(len(first[1]["codigo"]), 8)
        self.assertNotEqual(first[1]["codigo"].upper(), "ANA101")
        self.assertEqual((first[1]["hoy"], first[1]["total"]), (0, 0))

    def test_in_a_solo_con_sesion_de_vecino(self):
        self.assertEqual(self.public().get("/api/mi-invitacion")[0], 401)

    # IN-B
    def test_in_b_renovar(self):
        old = self.my_code()
        status, body, _ = self.neighbor().post("/api/mi-invitacion/renovar")
        self.assertEqual(status, 200)
        self.assertNotEqual(body["codigo"], old)
        self.assertEqual(self.code_of(self.public().get(f"/api/invitaciones/{old}")), "INVITE_NOT_FOUND")
        self.assertEqual(self.public().get(f"/api/invitaciones/{body['codigo']}")[0], 200)

    # IN-C
    def test_in_c_vista_previa(self):
        status, body, _ = self.public().get(f"/api/invitaciones/{self.my_code()}")
        self.assertEqual(status, 200)
        self.assertEqual(body["invita"], "Ana")
        self.assertEqual(body["zona"], self.store.zones["Z-LINCE-01"].name)
        text = json.dumps(body, ensure_ascii=False)
        self.assertNotIn("Torres", text)
        self.assertNotIn("phone", text.lower())
        self.assertNotIn("correo", text.lower())
        self.assertEqual(self.code_of(self.public().get("/api/invitaciones/inventado123")), "INVITE_NOT_FOUND")

    # IN-D
    def test_in_d_suspendido_no_invita(self):
        code = self.my_code()
        self.store.customers[101] = replace(self.store.customers[101], suspended=True)
        self.assertEqual(self.code_of(self.public().get(f"/api/invitaciones/{code}")), "INVITE_NOT_FOUND")
        self.assertEqual(self.code_of(self.start(code)), "INVITE_NOT_FOUND")


class EmailSignupTests(InviteBase):
    # IN-E
    def test_in_e_registro_con_correo(self):
        code = self.my_code()
        self.assertEqual(self.start(code)[0], 200)
        self.assertEqual(self.mailer.sent[-1][0], "lucia@correo.pe")
        self.assertNotIn("lucia@correo.pe", [c.email for c in self.store.customers.values()])  # todavía no hay cuenta
        client = self.public()
        status, body, _ = self.finish(code, client=client)
        self.assertEqual(status, 200, body)
        new = self.store.customers[body["usuario"]]
        self.assertEqual((new.zone_id, new.referred_by, new.name, new.phone), ("Z-LINCE-01", 101, "Lucía Ramos", "987654321"))
        self.assertIsNotNone(new.email_verified_at)
        self.assertIsNotNone(new.consent_at)
        self.assertEqual(client.get("/api/sesion")[1]["usuario"], new.customer_id)
        again = self.public()
        self.assertEqual(again.login(new.customer_id, NEW_PIN)[0], 200)

    # IN-F
    def test_in_f_validaciones(self):
        code = self.my_code()
        self.assertEqual(self.start(code)[0], 200)
        self.finish(code)
        before = (len(self.store.customers), len(self.mailer.sent), len(self.store.signups))
        cases = [({"celular": "812345678", "correo": "a@correo.pe"}, "INVALID_PHONE"),
                 ({"celular": "987654321", "correo": "b@correo.pe"}, "PHONE_ALREADY_REGISTERED"),
                 ({"celular": "987000111", "correo": "lucia@correo.pe"}, "EMAIL_ALREADY_REGISTERED"),
                 ({"celular": "987000111", "correo": "c@correo.pe", "consentimiento": False}, "CONSENT_REQUIRED"),
                 ({"celular": "987000111", "correo": "d@correo.pe", "nombre": "  "}, "NAME_REQUIRED"),
                 ({"celular": "987000111", "correo": "no-es-correo"}, "INVALID_EMAIL")]
        for changes, expected in cases:
            self.assertEqual(self.code_of(self.start(code, **changes)), expected, changes)
        self.assertEqual((len(self.store.customers), len(self.mailer.sent), len(self.store.signups)), before)

    # IN-G
    def test_in_g_codigo_malo(self):
        code = self.my_code()
        self.start(code)
        good = self.mailer.last_code()
        wrong = "000000" if good != "000000" else "111111"
        for _ in range(5):
            self.assertEqual(self.code_of(self.finish(code, code=wrong)), "INVALID_CODE")
        self.assertEqual(self.code_of(self.finish(code, code=good)), "INVALID_CODE")
        self.assertNotIn("lucia@correo.pe", [c.email for c in self.store.customers.values()])

    def test_in_g_codigo_vencido(self):
        code = self.my_code()
        self.start(code)
        good = self.mailer.last_code()
        self.now += timedelta(minutes=11)
        self.assertEqual(self.code_of(self.finish(code, code=good)), "INVALID_CODE")

    # IN-H
    def test_in_h_pin_flojo_no_gasta_el_codigo(self):
        code = self.my_code()
        self.start(code)
        good = self.mailer.last_code()
        self.assertEqual(self.code_of(self.finish(code, code=good, pin="123456")), "INVALID_PIN")
        self.assertEqual(self.finish(code, code=good, pin=NEW_PIN)[0], 200)

    def test_confirmar_sin_haber_pedido_codigo(self):
        code = self.my_code()
        self.assertEqual(self.code_of(self.finish(code, email="nadie@correo.pe", code="123456")), "INVALID_CODE")

    # IN-I
    def test_in_i_tope_diario(self):
        code = self.my_code()
        for i in range(20):
            self.assertEqual(self.register(code, i)[0], 200, i)
        self.assertEqual(self.code_of(self.register(code, 20)), "INVITE_LIMIT")
        self.now += timedelta(days=1, minutes=1)
        self.assertEqual(self.register(code, 20)[0], 200)
        self.assertEqual(self.neighbor().get("/api/mi-invitacion")[1]["total"], 21)

    # IN-K
    def test_in_k_avisos_sin_correo(self):
        zone = self.store.zones["Z-LINCE-01"]
        self.store.zones["Z-LINCE-01"] = replace(zone, admin_id=105)
        code = self.my_code()
        self.start(code)
        sent_before = len(self.mailer.sent)
        self.finish(code)
        for owner in (101, 105):
            mine = [n for n in self.store.notices if n.customer_id == owner and n.kind == "VECINO_NUEVO"]
            self.assertEqual(len(mine), 1, owner)
            self.assertIn("Lucía", mine[0].title)
            self.assertEqual(mine[0].email, "")
        self.assertEqual(len(self.mailer.sent), sent_before)

    def test_in_k_si_quien_invita_es_el_admin_un_solo_aviso(self):
        zone = self.store.zones["Z-LINCE-01"]
        self.store.zones["Z-LINCE-01"] = replace(zone, admin_id=101)
        code = self.my_code()
        self.start(code)
        self.finish(code)
        self.assertEqual(len([n for n in self.store.notices if n.kind == "VECINO_NUEVO"]), 1)

    # IN-L
    def test_in_l_queda_como_referido(self):
        code = self.my_code()
        self.start(code)
        new = self.store.customers[self.finish(code)[1]["usuario"]]
        self.assertEqual(new.referred_by, 101)

    # IN-M
    def test_in_m_pendientes(self):
        code = self.my_code()
        for i in range(200):
            self.assertEqual(self.start(code, celular=f"9100000{i:02d}"[:9], correo=f"p{i}@correo.pe")[0], 200, i)
        self.assertEqual(self.code_of(self.start(code, celular="999999999", correo="extra@correo.pe")), "SIGNUPS_FULL")
        self.now += timedelta(minutes=11)
        self.assertEqual(self.start(code, celular="999999999", correo="extra@correo.pe")[0], 200)

    # IN-N
    def test_in_n_no_toca_otras_cuentas(self):
        code = self.my_code()
        ana = self.store.customers[101]
        self.start(code)
        client = self.public()
        _, body, _ = self.finish(code, client=client)
        self.assertNotEqual(body["usuario"], 101)
        self.assertEqual(self.store.customers[101], ana)
        self.assertEqual(client.get("/api/sesion")[1]["usuario"], body["usuario"])

    def test_enlace_inexistente_en_el_registro(self):
        self.assertEqual(self.code_of(self.start("inventado123")), "INVITE_NOT_FOUND")
        self.assertEqual(self.code_of(self.finish("inventado123", code="123456")), "INVITE_NOT_FOUND")

    # IN-O (IN-08)
    def test_in_o_el_alta_manual_sigue_igual(self):
        from yapa_sdd import customers
        from yapa_sdd.seed import PILOT_ADMINS
        admin = sorted(PILOT_ADMINS)[0]
        customer, pin = customers.register_customer(self.store, "Lucía Ramos", "987654321", "Z-LINCE-01", True, by=admin,
                                                    now=self.now, email="lucia@correo.pe", referral="ANA101")
        self.assertEqual(customer.referred_by, 101)
        self.assertEqual(len(pin), 6)


@unittest.skipUnless(HAS_GOOGLE, "Entrar con Google necesita PyJWT y cryptography")
class GoogleSignupTests(InviteBase):
    def google(self, code, token=None, **changes):
        body = {"credential": mint(name="Lucía Gómez", sub="9999", email="lucia.g@gmail.com") if token is None else token,
                "celular": "987654321", "consentimiento": True} | changes
        client = self.public()
        return client, client.post(f"/api/invitaciones/{code}/google", body, with_csrf=False)

    # IN-J
    def test_in_j_registro_con_google(self):
        code = self.my_code()
        client, (status, body, _) = self.google(code)
        self.assertEqual(status, 200, body)
        new = self.store.customers[body["usuario"]]
        self.assertEqual((new.name, new.email, new.google_sub, new.zone_id, new.referred_by),
                         ("Lucía Gómez", "lucia.g@gmail.com", "9999", "Z-LINCE-01", 101))
        self.assertIsNotNone(new.email_verified_at)
        self.assertNotIn(("vecino", str(new.customer_id)), self.store.credentials)  # sin PIN
        self.assertTrue(client.get("/api/sesion")[1]["google_vinculado"])
        again = self.public()
        self.assertEqual(again.post("/api/sesion/google", {"credential": mint(name="Lucía Gómez", sub="9999",
                                                                               email="lucia.g@gmail.com")}, with_csrf=False)[0], 200)

    def test_in_j_validaciones(self):
        code = self.my_code()
        self.assertEqual(self.code_of(self.google(code, celular="12345")[1]), "INVALID_PHONE")
        self.assertEqual(self.code_of(self.google(code, consentimiento=False)[1]), "CONSENT_REQUIRED")
        self.assertEqual(self.code_of(self.google(code, token="no-es-un-token")[1]), "INVALID_GOOGLE_TOKEN")
        self.assertEqual(self.code_of(self.google("inventado123")[1]), "INVITE_NOT_FOUND")
        self.assertEqual(len(self.store.customers), 5)
        self.assertEqual(self.google(code)[1][0], 200)
        self.assertEqual(self.code_of(self.google(code, celular="987000222")[1]), "EMAIL_ALREADY_REGISTERED")
        self.assertEqual(self.code_of(self.google(code, token=mint(sub="9999", email="otra@gmail.com", name="X"),
                                                  celular="987000333")[1]), "GOOGLE_ALREADY_LINKED")
        self.assertEqual(self.code_of(self.google(code, token=mint(sub="8888", email="nueva@gmail.com", name="Y"))[1]),
                         "PHONE_ALREADY_REGISTERED")

    def test_in_j_cuenta_google_con_nombre_vacio_usa_el_correo(self):
        code = self.my_code()
        _, (status, body, _) = self.google(code, token=mint(sub="7777", email="sin.nombre@gmail.com", name=""))
        self.assertEqual(status, 200)
        self.assertEqual(self.store.customers[body["usuario"]].name, "sin.nombre")


if __name__ == "__main__":
    unittest.main()
