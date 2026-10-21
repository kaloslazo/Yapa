"""Iteración 50 · Endurecimiento antes de abrir. Spec: docs/desarrollo/50-endurecimiento-antes-de-abrir.md."""

import io
import json
import os
import tempfile
import unittest
from dataclasses import replace
from wsgiref.util import setup_testing_defaults

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, BASKET, PIN, WEDNESDAY
from test_cuenta_correo import FakeMailer
from test_demostracion import DEBUG, NOW, DemoBase
from web_client import WebClient, fast_hashing

from yapa_sdd import wallet
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.seed import pilot_store
from yapa_sdd.web import produccion
from yapa_sdd.web.api import create_api
from yapa_sdd.web.app import _save_photo, create_app

PNG = b"\x89PNG\r\n\x1a\nfoto-de-prueba"
NEW_PIN = "135790"


class FakeGoogle:
    client_id = "prueba"

    def verify(self, credential):
        return {"sub": "g-101", "email": "ana@gmail.com", "email_verified": True, "name": "Ana"}


def multipart(fields, files):
    boundary = "yapa-endurecimiento"
    parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode("utf-8")
             for k, v in fields.items()]
    for key, (filename, content) in files.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"'
                     f'\r\nContent-Type: image/png\r\n\r\n'.encode("utf-8") + content + b"\r\n")
    return b"".join(parts) + f"--{boundary}--\r\n".encode("utf-8"), f"multipart/form-data; boundary={boundary}"


def call(app, method, path, body=b"", content_type="", cookie=None, csrf=None, wsgi_input=None):
    environ = {}
    setup_testing_defaults(environ)
    environ.update({"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": "", "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": str(len(body)), "wsgi.input": wsgi_input or io.BytesIO(body)})
    if cookie:
        environ["HTTP_COOKIE"] = f"yapa_api={cookie}"
    if csrf:
        environ["HTTP_X_YAPA_CSRF"] = csrf
    result = {}

    def start_response(status, headers):
        result["status"], result["headers"] = int(status.split()[0]), dict(headers)

    raw = b"".join(app(environ, start_response))
    return result["status"], raw, result["headers"]


class Base(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        self.store.customers[101] = replace(self.store.customers[101], email="ana@gmail.com",
                                            email_verified_at=WEDNESDAY)
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.folder = tempfile.mkdtemp()
        self.mailer = FakeMailer()
        self.api = create_api(self.store, clock=lambda: WEDNESDAY, photo_dir=self.folder, mailer=self.mailer,
                              google=FakeGoogle(), background_mail=False)

    def neighbor(self, customer_id=101, pin=PIN):
        client = ApiClient(self.api)
        self.assertEqual(client.login(customer_id, pin)[0], 200)
        return client

    def admin(self):
        client = ApiClient(self.api)
        self.assertEqual(client.login(ADMIN, ADMIN_PASS, "admin")[0], 200)
        return client

    def photos(self):
        return os.listdir(self.folder)


class BodyLimitTests(Base):
    # SG-A
    def test_sg_a_cuerpo_enorme_se_rechaza_sin_leerlo(self):
        called = []

        class NoRead:
            def read(self, *args):
                raise AssertionError("no debía leer el cuerpo")

        def app(environ, start_response):
            called.append(True)
            start_response("200 OK", [])
            return [b""]

        environ = {}
        setup_testing_defaults(environ)
        environ.update({"REQUEST_METHOD": "POST", "PATH_INFO": "/api/sesion", "CONTENT_TYPE": "application/json",
                        "CONTENT_LENGTH": str(produccion.MAX_BODY + 1), "wsgi.input": NoRead()})
        result = {}
        body = b"".join(produccion.locked(app)(environ, lambda s, h: result.update(status=s)))
        self.assertEqual(result["status"][:3], "413")
        self.assertEqual(json.loads(body)["error"]["codigo"], "PAYLOAD_TOO_LARGE")
        self.assertEqual(called, [])

    # SG-B
    def test_sg_b_cuerpo_normal_pasa(self):
        raw = json.dumps({"tipo": "vecino", "usuario": "101", "secreto": PIN}).encode()
        status, _, _ = call(produccion.locked(self.api), "POST", "/api/sesion", raw, "application/json")
        self.assertEqual(status, 200)


class PhotoTests(Base):
    # SG-C
    def test_sg_c_foto_anonima_no_se_guarda(self):
        body, ctype = multipart({"usuario": "101"}, {"foto_archivo": ("x.png", PNG)})
        status, _, _ = call(self.api, "POST", "/api/pin/olvide", body, ctype)
        self.assertEqual(status, 200)
        self.assertEqual(self.photos(), [])

    # SG-D
    def test_sg_d_foto_en_ruta_sin_fotos_no_se_guarda(self):
        client = self.neighbor()
        client.post_file("/api/avisos/leer", {}, {"foto_archivo": ("x.png", PNG)})
        self.assertEqual(self.photos(), [])

    # SG-E
    def test_sg_e_foto_que_no_es_imagen_se_rechaza(self):
        status, body = self.admin().post_file("/api/admin/bolsas", {"pedido": "1"},
                                              {"foto_archivo": ("x.png", b"<html><script>alert(1)</script>")})
        self.assertEqual(status, 422)
        self.assertEqual(body["error"]["codigo"], "PHOTO_INVALID")
        self.assertEqual(self.photos(), [])

    # SG-F
    def test_sg_f_la_extension_sale_del_contenido(self):
        saved = _save_photo(self.folder, ("bolsa.jpg", PNG))
        self.assertRegex(saved, r"^fotos/[0-9a-f]{16}\.png$")
        self.assertEqual(len(self.photos()), 1)

    # SG-G
    def test_sg_g_web_html_sin_sesion_no_guarda_la_foto(self):
        web = WebClient(create_app(self.store, clock=lambda: WEDNESDAY, photo_dir=self.folder))
        status, headers, _ = web.post("/reclamos", {"articulo": "1:PAPA-AMARILLA"}, with_csrf=False,
                                      files={"foto_archivo": ("x.jpg", b"\xff\xd8\xff\xe0foto")})
        self.assertEqual((status, headers.get("Location")), (303, "/entrar"))
        self.assertEqual(self.photos(), [])


class SessionTests(Base):
    # SG-H
    def test_sg_h_recuperar_el_pin_cierra_las_sesiones(self):
        first, second = self.neighbor(), self.neighbor()
        anonymous = ApiClient(self.api)
        anonymous.post("/api/pin/olvide", {"usuario": "101"})
        status, body, _ = anonymous.post("/api/pin/restablecer",
                                         {"usuario": "101", "codigo": self.mailer.last_code(), "pin": NEW_PIN})
        self.assertEqual(status, 200, body)
        self.assertEqual(first.get("/api/sesion")[0], 401)
        self.assertEqual(second.get("/api/sesion")[0], 401)
        self.assertEqual(ApiClient(self.api).login(101, NEW_PIN)[0], 200)

    # SG-I
    def test_sg_i_cambiar_el_pin_cierra_las_otras(self):
        here, other = self.neighbor(), self.neighbor()
        status, body, _ = here.post("/api/pin", {"actual": PIN, "nuevo": NEW_PIN})
        self.assertEqual(status, 200, body)
        self.assertEqual(here.get("/api/sesion")[0], 200)
        self.assertEqual(other.get("/api/sesion")[0], 401)

    # SG-J
    def test_sg_j_pin_nuevo_del_admin_cierra_la_sesion(self):
        client = self.neighbor()
        self.assertEqual(self.admin().post("/api/admin/vecinos/101/pin")[0], 200)
        self.assertEqual(client.get("/api/sesion")[0], 401)

    # SG-K
    def test_sg_k_crear_el_pin_deja_la_sesion(self):
        self.store.customers[101] = replace(self.store.customers[101], google_sub="g-101")
        del self.store.credentials[("vecino", "101")]
        client = ApiClient(self.api)
        status, me, _ = client.post("/api/sesion/google", {"credential": "x"}, with_csrf=False)
        self.assertEqual(status, 200, me)
        client.csrf = me["csrf"]
        self.assertEqual(client.post("/api/pin/crear", {"pin": NEW_PIN})[0], 200)
        self.assertEqual(client.get("/api/sesion")[0], 200)

    # SG-L
    def test_sg_l_la_web_html_tambien_cierra(self):
        web = WebClient(create_app(self.store, clock=lambda: WEDNESDAY))
        web.login(101, PIN)
        self.assertEqual(web.get("/cuenta")[0], 200)
        self.neighbor().post("/api/pin", {"actual": PIN, "nuevo": NEW_PIN})
        status, headers, _ = web.get("/cuenta")
        self.assertEqual((status, headers.get("Location")), (303, "/entrar"))


class ViewAsMoneyTests(DemoBase):
    def setUp(self):
        super().setUp()
        self.store = self.seed()
        self.api = create_api(self.store, clock=lambda: NOW)

    def viewing(self, customer_id):
        client = ApiClient(self.api)
        self.assertEqual(client.login("debug-global", DEBUG, "admin")[0], 200)
        self.assertEqual(client.post("/api/admin/ver-como", {"usuario": customer_id})[0], 200)
        return client

    # SG-M
    def test_sg_m_ver_como_no_saca_dinero(self):
        client = self.viewing(101)
        balance = wallet.balance(self.store, 101)
        refunds = len(self.store.refunds)
        orders = {k: v.status for k, v in self.store.orders.items()}
        zone = next(z for z in self.store.zones.values() if z.admin_id == 101)
        mine = next(o.order_id for o in self.store.orders.values() if o.customer_id == 101)
        for path, body in (("/api/saldo/devolucion", {"monto": "0.10"}),
                           (f"/api/pedidos/{mine}/cancelar", {}),
                           (f"/api/zonas/{zone.zone_id}/transferir", {"nuevo": 105})):
            status, data, _ = client.post(path, body)
            self.assertEqual((status, data["error"]["codigo"]), (422, "DEBUG_SESSION_READONLY"), path)
        self.assertEqual(wallet.balance(self.store, 101), balance)
        self.assertEqual({k: v.status for k, v in self.store.orders.items()}, orders)
        self.assertEqual(self.store.zones[zone.zone_id].admin_id, 101)
        self.assertEqual(len(self.store.refunds), refunds)

    # SG-N
    def test_sg_n_ver_como_sigue_sirviendo(self):
        client = self.viewing(105)
        status, quote, _ = client.post("/api/cotizar", {"lineas": BASKET})
        self.assertEqual(status, 200, quote)


if __name__ == "__main__":
    unittest.main()
