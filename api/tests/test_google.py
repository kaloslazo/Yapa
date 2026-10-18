"""Iteración 41: Entrar con Google (docs/desarrollo/41-entrar-con-google.md).

Los tokens se firman de verdad con una llave RSA propia que se presenta como si fuera la de Google:
se prueba la verificación real, no un doble que siempre dice que sí.
"""

import base64
import hashlib
import hmac
import json
import time
import unittest
from dataclasses import replace

try:
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
except ImportError:  # S-214: dependencia opcional
    raise unittest.SkipTest("Entrar con Google necesita PyJWT y cryptography (dependencia opcional)")

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, PIN, WEDNESDAY
from test_cuenta_correo import FakeMailer
from web_client import fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.google_identity import GoogleVerifier
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

CLIENT_ID = "yapa-prueba.apps.googleusercontent.com"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
JWKS = {"keys": [json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key())) | {"kid": "k1", "alg": "RS256", "use": "sig"}]}


def mint(key=KEY, **changes):
    now = int(time.time())
    claims = {"iss": "https://accounts.google.com", "aud": CLIENT_ID, "sub": "1111", "email": "ana.g@gmail.com",
              "email_verified": True, "iat": now, "exp": now + 3600} | changes
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": "k1"})


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class GoogleBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        self.store.customers[101] = replace(self.store.customers[101], phone="987654321")
        set_pin(self.store, 101, PIN)
        set_pin(self.store, 104, "246802")
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.mailer = FakeMailer()
        self.api = self.make_api(GoogleVerifier(CLIENT_ID, jwks_provider=lambda: JWKS))

    def make_api(self, google):
        return create_api(self.store, clock=lambda: WEDNESDAY, mailer=self.mailer, google=google)

    def neighbor(self, customer_id=101, pin=PIN, api=None):
        client = ApiClient(api or self.api)
        client.login(customer_id, pin, "vecino")
        return client

    def link(self, token=None, customer_id=101, pin=PIN, api=None):
        return self.neighbor(customer_id, pin, api).post("/api/cuenta/google", {"credential": mint() if token is None else token})

    def enter(self, token=None, api=None):
        client = ApiClient(api or self.api)
        return client, client.post("/api/sesion/google", {"credential": mint() if token is None else token}, with_csrf=False)

    def code(self, response):
        return response[1]["error"]["codigo"]


class LinkAndEnterTests(GoogleBase):
    # GO-A
    def test_go_a_vincular(self):
        status, body, _ = self.link()
        self.assertEqual(status, 200, body)
        self.assertEqual(self.store.customers[101].google_sub, "1111")
        self.assertTrue(self.neighbor().get("/api/sesion")[1]["google_vinculado"])

    # GO-B
    def test_go_b_entrar_despues_de_vincular(self):
        self.link()
        client, (status, body, _) = self.enter()
        self.assertEqual((status, body["usuario"]), (200, 101))
        status, body, _ = client.get("/api/sesion")
        self.assertEqual((status, body["usuario"]), (200, 101))

    # GO-C
    def test_go_c_cuenta_sin_vincular(self):
        _, response = self.enter(mint(sub="2222"))
        self.assertEqual((response[0], self.code(response)), (422, "GOOGLE_NOT_LINKED"))

    # GO-R
    def test_go_r_la_respuesta_no_lleva_secretos(self):
        self.link()
        token = mint()
        _, (_, body, _) = self.enter(token)
        text = json.dumps(body)
        self.assertNotIn(token, text)
        self.assertNotIn("1111", text)

    # GO-O
    def test_go_o_desvincular(self):
        client = self.neighbor()
        client.post("/api/cuenta/google", {"credential": mint()})
        status, body, _ = client.post("/api/cuenta/google/desvincular")
        self.assertEqual(status, 200, body)
        _, response = self.enter()
        self.assertEqual(self.code(response), "GOOGLE_NOT_LINKED")
        self.assertEqual(ApiClient(self.api).post("/api/sesion", {"tipo": "vecino", "usuario": "101", "secreto": PIN},
                                                  with_csrf=False)[0], 200)

    # GO-P
    def test_go_p_roles(self):
        status, body, _ = ApiClient(self.api).post("/api/cuenta/google", {"credential": mint()}, with_csrf=False)
        self.assertEqual((status, body["error"]["codigo"]), (401, "LOGIN_REQUIRED"))
        admin = ApiClient(self.api)
        admin.login(ADMIN, ADMIN_PASS, "admin")
        status, body, _ = admin.post("/api/cuenta/google", {"credential": mint()})
        self.assertEqual((status, body["error"]["codigo"]), (403, "FORBIDDEN"))


class TokenCheckTests(GoogleBase):
    def assertRejected(self, token):
        self.assertEqual(self.code(self.link(token)), "INVALID_GOOGLE_TOKEN")
        _, response = self.enter(token)
        self.assertEqual(self.code(response), "INVALID_GOOGLE_TOKEN")

    # GO-D
    def test_go_d_firma_ajena(self):
        self.assertRejected(mint(key=OTHER_KEY))

    # GO-E
    def test_go_e_otra_audiencia(self):
        self.assertRejected(mint(aud="otro-proyecto.apps.googleusercontent.com"))

    # GO-F
    def test_go_f_otro_emisor(self):
        self.assertRejected(mint(iss="https://evil.example.com"))

    # GO-G
    def test_go_g_vencido(self):
        self.assertRejected(mint(iat=int(time.time()) - 7200, exp=int(time.time()) - 3600))

    # GO-H
    def test_go_h_correo_sin_verificar(self):
        self.assertRejected(mint(email_verified=False))

    # GO-I
    def test_go_i_algoritmos_prohibidos(self):
        now = int(time.time())
        claims = {"iss": "https://accounts.google.com", "aud": CLIENT_ID, "sub": "1111", "email": "ana.g@gmail.com",
                  "email_verified": True, "iat": now, "exp": now + 3600}
        unsigned = jwt.encode(claims, None, algorithm="none", headers={"kid": "k1"})
        header = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": "k1"}).encode())
        payload = b64(json.dumps(claims).encode())
        signature = b64(hmac.new(b"secreto", f"{header}.{payload}".encode(), hashlib.sha256).digest())
        self.assertRejected(unsigned)
        self.assertRejected(f"{header}.{payload}.{signature}")
        self.assertRejected("esto-no-es-un-token")
        self.assertRejected("")


class SettingsTests(GoogleBase):
    # GO-J
    def test_go_j_sin_configurar(self):
        api = self.make_api(None)
        self.assertEqual(self.code(self.link(api=api)), "GOOGLE_NOT_CONFIGURED")
        _, response = self.enter(api=api)
        self.assertEqual(self.code(response), "GOOGLE_NOT_CONFIGURED")

    # GO-Q
    def test_go_q_estado(self):
        self.assertEqual(ApiClient(self.api).get("/api/estado")[1]["google_client_id"], CLIENT_ID)
        self.assertIsNone(ApiClient(self.make_api(None)).get("/api/estado")[1]["google_client_id"])


class EmailAndUniquenessTests(GoogleBase):
    # GO-K
    def test_go_k_adopta_el_correo_de_google(self):
        self.link()
        customer = self.store.customers[101]
        self.assertEqual(customer.email, "ana.g@gmail.com")
        self.assertIsNotNone(customer.email_verified_at)

    # GO-L
    def test_go_l_no_pisa_un_correo_verificado(self):
        client = self.neighbor()
        client.post("/api/cuenta/correo", {"correo": "ana@gmail.com"})
        client.post("/api/cuenta/correo/verificar", {"codigo": self.mailer.last_code()})
        self.assertEqual(self.link()[0], 200)
        self.assertEqual(self.store.customers[101].email, "ana@gmail.com")
        self.assertEqual(self.store.customers[101].google_sub, "1111")

    # GO-M
    def test_go_m_correo_ya_usado_por_otro(self):
        self.store.customers[104] = replace(self.store.customers[104], email="ana.g@gmail.com")
        self.assertEqual(self.link()[0], 200)
        customer = self.store.customers[101]
        self.assertEqual((customer.email, customer.google_sub), (None, "1111"))

    # GO-N
    def test_go_n_una_cuenta_un_vecino(self):
        self.assertEqual(self.link()[0], 200)
        status, body, _ = self.link(customer_id=104, pin="246802")
        self.assertEqual((status, body["error"]["codigo"]), (422, "GOOGLE_ALREADY_LINKED"))
        self.assertIsNone(self.store.customers[104].google_sub)

    # S-213: vincular otra cuenta reemplaza la anterior
    def test_go_n2_vincular_otra_cuenta_reemplaza_la_anterior(self):
        self.link(mint(sub="1111"))
        self.link(mint(sub="2222", email="otra@gmail.com"))
        self.assertEqual(self.store.customers[101].google_sub, "2222")
        _, response = self.enter(mint(sub="1111"))
        self.assertEqual(self.code(response), "GOOGLE_NOT_LINKED")


if __name__ == "__main__":
    unittest.main()
