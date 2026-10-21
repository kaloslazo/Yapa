"""Iteración 51 · Cierre de huecos para pasar a main. Spec: docs/desarrollo/51-cierre-de-huecos-para-main.md."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, PIN, WEDNESDAY
from test_cuenta_correo import FakeMailer
from test_demostracion import DEBUG, NOW, DemoBase
from web_client import WebClient, fast_hashing

from yapa_sdd import auth, invitations
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.domain import Customer
from yapa_sdd.mailer import MailError, SmtpMailer, mailer_from_env
from yapa_sdd.seed import pilot_store
from yapa_sdd.web import produccion
from yapa_sdd.web.api import create_api
from yapa_sdd.web.app import create_app
from yapa_sdd.web.produccion import client_ip


def from_ip(client, ip, forwarded=None):
    client.extra = {"REMOTE_ADDR": ip}
    if forwarded:
        client.extra["HTTP_X_FORWARDED_FOR"] = forwarded
    return client


class Base(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.clock = [WEDNESDAY]
        self.mailer = FakeMailer()
        self.api = create_api(self.store, clock=lambda: self.clock[0], mailer=self.mailer, background_mail=False)

    def client(self, ip="203.0.113.5"):
        return from_ip(ApiClient(self.api), ip)

    def code_of(self, response):
        return response[1]["error"]["codigo"]


class ClientIpTests(unittest.TestCase):
    # SG-O
    def test_sg_o_direccion_del_cliente(self):
        self.assertEqual(client_ip({"REMOTE_ADDR": "203.0.113.5"}), "203.0.113.5")
        self.assertEqual(client_ip({"REMOTE_ADDR": "127.0.0.1", "HTTP_X_FORWARDED_FOR": "1.1.1.1, 198.51.100.7"}),
                         "198.51.100.7")
        self.assertEqual(client_ip({"REMOTE_ADDR": "::1", "HTTP_X_FORWARDED_FOR": "198.51.100.7"}), "198.51.100.7")
        self.assertEqual(client_ip({"REMOTE_ADDR": "203.0.113.5", "HTTP_X_FORWARDED_FOR": "198.51.100.7"}),
                         "203.0.113.5")


class LoginThrottleTests(Base):
    # SG-P
    def test_sg_p_treinta_fallos_desde_una_direccion(self):
        client = self.client()
        for user in range(1000, 1030):
            self.assertEqual(client.login(user, "000000")[0], 422)
        status, body, _ = client.login(101, PIN)
        self.assertEqual((status, body["error"]["codigo"]), (429, "TOO_MANY_ATTEMPTS"))
        self.assertEqual(self.client("198.51.100.9").login(101, PIN)[0], 200)
        self.clock[0] += timedelta(minutes=16)
        self.assertEqual(client.login(101, PIN)[0], 200)

    def test_sg_p_detras_del_proxy_cuenta_la_direccion_real(self):
        for n in range(30):
            from_ip(ApiClient(self.api), "127.0.0.1", "198.51.100.1").login(1000 + n, "000000")
        self.assertEqual(from_ip(ApiClient(self.api), "127.0.0.1", "198.51.100.1").login(101, PIN)[0], 429)
        self.assertEqual(from_ip(ApiClient(self.api), "127.0.0.1", "198.51.100.2").login(101, PIN)[0], 200)

    def test_sg_p_restablecer_con_codigo_cuenta_como_fallo(self):
        client = self.client()
        for _ in range(30):
            client.post("/api/pin/restablecer", {"usuario": "101", "codigo": "000000", "pin": "135790"}, with_csrf=False)
        self.assertEqual(client.login(101, PIN)[0], 429)

    # SG-Q
    def test_sg_q_web_html(self):
        web = from_ip(WebClient(create_app(self.store, clock=lambda: self.clock[0])), "203.0.113.5")
        for user in range(1000, 1030):
            web.login(user, "000000")
        self.assertEqual(web.login(101, PIN)[0], 429)


class MailThrottleTests(Base):
    # SG-R
    def test_sg_r_diez_correos_por_direccion(self):
        for n in range(11):
            customer_id = 300 + n
            self.store.add_customer(Customer(customer_id, f"Vecino {n}", "Z-JM-01", email=f"v{n}@gmail.com",
                                             email_verified_at=WEDNESDAY))
        client = self.client()
        for n in range(11):
            status, _, _ = client.post("/api/pin/olvide", {"usuario": str(300 + n)}, with_csrf=False)
            self.assertEqual(status, 200)
        self.assertEqual(len(self.mailer.sent), 10)

    # SG-S
    def test_sg_s_diez_codigos_por_enlace(self):
        code = invitations.link_for(self.store, 101, WEDNESDAY)["codigo"]
        results = []
        for n in range(11):
            body = {"nombre": f"Vecino {n}", "celular": f"9{n:08d}", "correo": f"nuevo{n}@gmail.com",
                    "consentimiento": True}
            results.append(self.client(f"198.51.100.{n}").post(f"/api/invitaciones/{code}/correo", body,
                                                               with_csrf=False))
        self.assertEqual([r[0] for r in results[:10]], [200] * 10)
        self.assertEqual(self.code_of(results[10]), "INVITE_CODE_LIMIT")


class ZoneListTests(Base):
    # SG-T
    def test_sg_t_zonas_segun_quien_mira(self):
        zone = self.store.zones["Z-LINCE-01"]
        self.store.zones["Z-LINCE-01"] = replace(zone, lat=-12.086123, lon=-77.034567, reception_contact="987654321")
        public = {z["id"]: z for z in self.client().get("/api/zonas")[1]["zonas"]}["Z-LINCE-01"]
        self.assertNotIn("contacto", public)
        self.assertNotIn("admin", public)
        self.assertEqual((public["lat"], public["lon"]), (-12.086, -77.035))
        neighbor = self.client()
        neighbor.login(101, PIN)
        mine = {z["id"]: z for z in neighbor.get("/api/zonas")[1]["zonas"]}["Z-LINCE-01"]
        self.assertNotIn("contacto", mine)
        self.assertNotIn("admin", mine)
        admin = self.client()
        admin.login(ADMIN, ADMIN_PASS, "admin")
        full = {z["id"]: z for z in admin.get("/api/zonas")[1]["zonas"]}["Z-LINCE-01"]
        self.assertEqual((full["contacto"], full["lat"]), ("987654321", -12.086123))


class ServerMailerTests(unittest.TestCase):
    # SG-U
    def test_sg_u_sin_smtp_en_servidor_no_escribe_el_codigo(self):
        out = io.StringIO()
        with redirect_stdout(out):
            mailer = mailer_from_env({}, server=True)
            with self.assertRaises(MailError):
                mailer.send("ana@gmail.com", "Recupera tu PIN", "Tu código es 123456.")
        self.assertNotIn("123456", out.getvalue())
        env = {"YAPA_SMTP_USER": "yapa@gmail.com", "YAPA_SMTP_PASSWORD": "x"}
        self.assertIsInstance(mailer_from_env(env, server=True), SmtpMailer)


class HeaderTests(Base):
    def app(self, secure):
        folder = tempfile.mkdtemp()
        (Path(folder) / "index.html").write_text("<html><title>Yapa</title></html>", encoding="utf-8")
        html = create_app(self.store, clock=lambda: self.clock[0])
        return produccion.compose(self.api, html, folder, secure=secure)

    def headers(self, app, path):
        environ = {}
        setup_testing_defaults(environ)
        environ.update({"REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": ""})
        found = {}
        b"".join(app(environ, lambda status, headers: found.update(dict(headers))))
        return found

    # SG-V
    def test_sg_v_cabeceras_en_toda_respuesta(self):
        app = self.app(secure=True)
        for path in ("/api/estado", "/", "/salud"):
            headers = self.headers(app, path)
            self.assertIn("default-src 'self'", headers.get("Content-Security-Policy", ""), path)
            self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff", path)
            self.assertIn("max-age=31536000", headers.get("Strict-Transport-Security", ""), path)
        self.assertNotIn("Strict-Transport-Security", self.headers(self.app(secure=False), "/api/estado"))

    def test_sg_v_csp_permite_google_y_mapas(self):
        csp = self.headers(self.app(secure=False), "/")["Content-Security-Policy"]
        self.assertIn("https://accounts.google.com/gsi/client", csp)
        self.assertIn("https://tile.openstreetmap.org", csp)
        self.assertIn("frame-ancestors 'none'", csp)


class SessionPurgeTests(Base):
    # SG-W
    def test_sg_w_las_vencidas_se_borran(self):
        old = self.client()
        old.login(101, PIN)
        self.assertEqual(len(self.api.sessions), 1)
        self.clock[0] += timedelta(hours=9)
        self.client().login(ADMIN, ADMIN_PASS, "admin")
        self.assertEqual(len(self.api.sessions), 1)


class ViewAsReturnTests(DemoBase):
    # SG-X
    def test_sg_x_no_vuelve_si_la_clave_del_admin_cambio(self):
        store = self.seed()
        api = create_api(store, clock=lambda: NOW)
        client = ApiClient(api)
        client.login("debug-global", DEBUG, "admin")
        client.post("/api/admin/ver-como", {"usuario": 101})
        auth.set_admin_password(store, "debug-global", "otra-clave-de-depuracion")
        self.assertEqual(self.code_of(client.post("/api/sesion/volver")), "NOT_VIEWING_AS")


if __name__ == "__main__":
    unittest.main()
