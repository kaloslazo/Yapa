"""Iteración 44 · Lista para producción. Spec: docs/desarrollo/44-produccion.md."""

import io
import tempfile
import threading
import time
import unittest
from datetime import datetime
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd import auth
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.seed import pilot_store
from yapa_sdd.web import produccion
from yapa_sdd.web.api import create_api

ENV = {"YAPA_ADMIN_USUARIO": "jefa-yapa", "YAPA_ADMIN_CLAVE": "clave-larga-2026"}

def call(app, method="GET", path="/"):
    environ = {}
    setup_testing_defaults(environ)
    environ.update({"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "", "wsgi.input": io.BytesIO(b"")})
    result = {}

    def start_response(status, headers):
        result["status"] = int(status.split()[0])
        result["headers"] = dict(headers)

    body = b"".join(app(environ, start_response))
    return result["status"], result["headers"], body


def stub(label):
    def app(environ, start_response):
        raw = label.encode()
        start_response("200 OK", [("Content-Type", "text/plain"), ("Content-Length", str(len(raw)))])
        return [raw]
    return app


class CredencialesTest(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()

    def code_of(self, action):
        with self.assertRaises(BusinessRuleError) as raised:
            action()
        return raised.exception.code

    def test_pr_a_sin_demo_en_modo_servidor(self):
        produccion.prepare_server_credentials(self.store, ENV)
        self.assertEqual(self.store.credentials.keys() & {("admin", "admin-yapa")}, set())
        self.assertEqual([key for key in self.store.credentials if key[0] == "vecino"], [])
        self.assertEqual(self.code_of(lambda: auth.authenticate(self.store, "admin", "admin-yapa", "yapa-admin-2026",
                                                                 datetime.now())), "INVALID_CREDENTIALS")

    def test_pr_b_el_admin_real_entra(self):
        produccion.prepare_server_credentials(self.store, ENV)
        now = datetime.now()
        self.assertEqual(auth.authenticate(self.store, "admin", "jefa-yapa", "clave-larga-2026", now), "jefa-yapa")
        self.assertEqual(self.code_of(lambda: auth.authenticate(self.store, "admin", "jefa-yapa", "otra-clave-larga", now)),
                         "INVALID_CREDENTIALS")

    def test_pr_c_falta_el_admin(self):
        for env in ({}, {"YAPA_ADMIN_USUARIO": "jefa-yapa"}, {"YAPA_ADMIN_CLAVE": "clave-larga-2026"}):
            self.assertEqual(self.code_of(lambda: produccion.prepare_server_credentials(pilot_store(), env)),
                             "ADMIN_NOT_CONFIGURED")

    def test_pr_d_ya_hay_admin_en_la_base(self):
        set_admin_password(self.store, "jefa-yapa", "clave-larga-2026")
        produccion.prepare_server_credentials(self.store, {})
        self.assertEqual(auth.authenticate(self.store, "admin", "jefa-yapa", "clave-larga-2026", datetime.now()),
                         "jefa-yapa")

    def test_pr_e_clave_corta(self):
        env = {"YAPA_ADMIN_USUARIO": "jefa-yapa", "YAPA_ADMIN_CLAVE": "corta"}
        self.assertEqual(self.code_of(lambda: produccion.prepare_server_credentials(self.store, env)), "INVALID_PASSWORD")

    def test_pr_f_escuchar_fuera_sin_base(self):
        self.assertEqual(self.code_of(lambda: produccion.check_listen("0.0.0.0", None)), "UNSAFE_LISTEN")
        produccion.check_listen("0.0.0.0", "yapa.db")
        produccion.check_listen("127.0.0.1", None)


class CookieTest(unittest.TestCase):
    def cookies(self, secure):
        fast_hashing(self)
        store = pilot_store()
        set_pin(store, 101, "482915")
        client = ApiClient(create_api(store, secure_cookie=secure))
        _, _, login = client.login(101, "482915")
        _, _, logout = client.request("DELETE", "/api/sesion")
        return login["Set-Cookie"], logout["Set-Cookie"]

    def test_pr_g_cookie_segura(self):
        entrar, salir = self.cookies(True)
        self.assertIn("Secure", entrar.split("; "))
        self.assertIn("Secure", salir.split("; "))

    def test_pr_g_sin_https_no_hay_secure(self):
        entrar, salir = self.cookies(False)
        self.assertNotIn("Secure", entrar.split("; "))
        self.assertNotIn("Secure", salir.split("; "))

    def test_pr_g_la_direccion_publica_activa_secure(self):
        self.assertTrue(produccion.secure_cookie({"YAPA_PUBLIC_URL": "https://holayapa.app"}))
        self.assertFalse(produccion.secure_cookie({"YAPA_PUBLIC_URL": "http://localhost:5173"}))
        self.assertFalse(produccion.secure_cookie({}))


class WebTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "secreto.txt").write_text("NO SE ENTREGA")
        static = root / "dist"
        (static / "assets").mkdir(parents=True)
        (static / "index.html").write_text("<html>portada</html>")
        (static / "assets" / "a.js").write_text("console.log(1)")
        self.app = produccion.compose(stub("API"), stub("HTML"), str(static))

    def test_pr_h_salud(self):
        status, headers, body = call(self.app, "GET", "/salud")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"ok": true}')
        self.assertIn("application/json", headers["Content-Type"])

    def test_pr_i_web_estatica(self):
        self.assertEqual(call(self.app, "GET", "/")[2], b"<html>portada</html>")
        self.assertEqual(call(self.app, "GET", "/ruta/inventada")[2], b"<html>portada</html>")
        status, headers, body = call(self.app, "GET", "/assets/a.js")
        self.assertEqual((status, body), (200, b"console.log(1)"))
        self.assertIn("javascript", headers["Content-Type"])
        self.assertEqual(call(self.app, "GET", "/api/sesion")[2], b"API")
        self.assertEqual(call(self.app, "GET", "/assets/falta.js")[0], 404)  # un archivo que falta no es la portada

    def test_pr_i_sin_carpeta_sigue_la_pagina_de_siempre(self):
        app = produccion.compose(stub("API"), stub("HTML"), None)
        self.assertEqual(call(app, "GET", "/")[2], b"HTML")
        self.assertEqual(call(app, "GET", "/salud")[0], 200)

    def test_pr_j_nada_fuera_de_la_carpeta(self):
        for path in ("/../secreto.txt", "/../secreto", "/%2e%2e/secreto.txt", "/..%5csecreto.txt", "/assets/../../secreto.txt",
                     "/..\\secreto.txt", "/assets/a.js\x00.png"):
            status, _, body = call(self.app, "GET", path)
            self.assertEqual(status, 404, path)
            self.assertNotIn(b"NO SE ENTREGA", body, path)

    def test_pr_k_solo_lectura(self):
        self.assertEqual(call(self.app, "POST", "/")[0], 405)
        self.assertEqual(call(self.app, "DELETE", "/assets/a.js")[0], 405)
        self.assertEqual(call(self.app, "HEAD", "/")[0], 200)

    def test_pr_l_cabeceras(self):
        _, headers, _ = call(self.app, "GET", "/")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(headers["Cache-Control"], "no-cache")
        self.assertIn("max-age=3600", call(self.app, "GET", "/assets/a.js")[1]["Cache-Control"])


class CerrojoTest(unittest.TestCase):
    def test_pr_m_una_peticion_a_la_vez(self):
        inside, peak, lock = [0], [0], threading.Lock()

        def slow(environ, start_response):
            with lock:
                inside[0] += 1
                peak[0] = max(peak[0], inside[0])
            time.sleep(0.02)
            with lock:
                inside[0] -= 1
            start_response("200 OK", [("Content-Length", "2")])
            return [b"ok"]

        app = produccion.locked(slow)
        threads = [threading.Thread(target=lambda: [call(app) for _ in range(5)]) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(peak[0], 1)


if __name__ == "__main__":
    unittest.main()
