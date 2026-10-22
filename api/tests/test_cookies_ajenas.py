"""Iteración 53 · La sesión no se pierde por cookies de otros servicios. Spec: docs/desarrollo/53-cookies-de-otros-sitios.md."""

import unittest

from api_client import ApiClient
from test_api import PIN
from web_client import WebClient, fast_hashing

from yapa_sdd.auth import set_pin
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api
from yapa_sdd.web.app import create_app

GOOGLE = 'g_state={"i_l":0,"i_ll":1792686000000}'  # la cookie que deja el botón de Google


class ApiCookiesTest(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        self.client = ApiClient(create_api(self.store))
        status, _, _ = self.client.login(101, PIN)
        self.assertEqual(status, 200)
        self.token = self.client.cookie

    def session_with(self, cookie_header):
        self.client.cookie = None
        self.client.extra = {"HTTP_COOKIE": cookie_header}
        status, _, _ = self.client.get("/api/sesion")
        return status

    def test_ck_a_google_antes_no_saca_la_sesion(self):
        self.assertEqual(self.session_with(f"{GOOGLE}; yapa_api={self.token}"), 200)

    def test_ck_b_google_despues_no_saca_la_sesion(self):
        self.assertEqual(self.session_with(f"yapa_api={self.token}; {GOOGLE}"), 200)

    def test_ck_c_sin_cookie_de_yapa_no_hay_sesion(self):
        self.assertEqual(self.session_with(GOOGLE), 401)


class WebCookiesTest(unittest.TestCase):
    def test_ck_d_web_html_con_google_antes(self):
        fast_hashing(self)
        store = pilot_store()
        set_pin(store, 101, PIN)
        client = WebClient(create_app(store))
        status, _, _ = client.login(101, PIN)
        self.assertEqual(status, 303)
        token, client.cookie = client.cookie, None
        client.extra = {"HTTP_COOKIE": f"{GOOGLE}; yapa_sesion={token}"}
        status, _, html = client.get("/cuenta")
        self.assertEqual(status, 200)
        self.assertNotIn('name="secreto"', html)


if __name__ == "__main__":
    unittest.main()
