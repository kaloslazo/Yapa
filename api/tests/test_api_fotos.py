"""Iteración 33: el admin ve las fotos guardadas (docs/desarrollo/33-admin-foto-confirmaciones.md)."""

import json
import tempfile
import unittest
from pathlib import Path

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, BASKET, PIN, SATURDAY, WEDNESDAY

from web_client import fast_hashing
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

JPEG = b"\xff\xd8\xff\xe0foto-de-prueba"
NAME = "0123456789abcdef"


class PhotoTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.folder = tempfile.mkdtemp()
        self.now = WEDNESDAY
        self.api = create_api(self.store, clock=lambda: self.now, photo_dir=self.folder)

    def client(self, user, secret, kind):
        client = ApiClient(self.api)
        client.login(user, secret, kind)
        return client

    def admin(self):
        return self.client(ADMIN, ADMIN_PASS, "admin")

    def error_code(self, client, path):
        status, body, _ = client.get_raw(path)
        return status, json.loads(body)["error"]["codigo"]

    # FA-A
    def test_fa_a_admin_ve_una_foto_guardada(self):
        (Path(self.folder) / f"{NAME}.jpg").write_bytes(JPEG)
        status, body, headers = self.admin().get_raw(f"/api/admin/foto?ruta=fotos/{NAME}.jpg")
        self.assertEqual(status, 200)
        self.assertEqual(body, JPEG)
        self.assertEqual(headers["Content-Type"], "image/jpeg")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["Cache-Control"], "private, no-store")

    # FA-B
    def test_fa_b_sin_sesion(self):
        self.assertEqual(self.error_code(ApiClient(self.api), f"/api/admin/foto?ruta=fotos/{NAME}.jpg"),
                         (401, "LOGIN_REQUIRED"))

    # FA-C
    def test_fa_c_vecino_no_puede(self):
        self.assertEqual(self.error_code(self.client(101, PIN, "vecino"), f"/api/admin/foto?ruta=fotos/{NAME}.jpg"),
                         (403, "FORBIDDEN"))

    # FA-D, FA-E, FA-F, FA-H
    def test_fa_d_rutas_invalidas(self):
        admin = self.admin()
        for ruta in ("fotos/../secreto.txt", f"fotos/{NAME}.txt", "", "/etc/passwd", "C:/Windows/win.ini",
                     f"fotos/{NAME}/../{NAME}.jpg", f"fotos/{NAME}.jpg%00.png", f"otra/{NAME}.jpg", "fotos/ABC.jpg"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.error_code(admin, f"/api/admin/foto?ruta={ruta}"), (422, "INVALID_INPUT"))
        self.assertEqual(self.error_code(admin, "/api/admin/foto"), (422, "INVALID_INPUT"))

    # FA-G
    def test_fa_g_foto_que_no_existe(self):
        self.assertEqual(self.error_code(self.admin(), f"/api/admin/foto?ruta=fotos/{NAME}.jpg"),
                         (404, "PHOTO_NOT_FOUND"))

    # FA-I
    def test_fa_i_foto_subida_se_puede_ver(self):
        for customer_id in range(801, 809):
            from yapa_sdd.domain import Customer
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", "Z-JM-01"))
            set_pin(self.store, customer_id, PIN)
            self.client(customer_id, PIN, "vecino").post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})
        admin = self.admin()
        for order_id in range(1, 9):
            admin.post(f"/api/admin/pedidos/{order_id}/verificar")
        self.now = SATURDAY
        admin = self.admin()
        status, saved = admin.post_file("/api/admin/bolsas", {"pedido": "1"}, {"foto_archivo": ("bolsa.jpg", JPEG)})
        self.assertEqual(status, 200)
        self.assertRegex(saved["foto"], r"^fotos/[0-9a-f]{16}\.jpg$")
        status, body, _ = admin.get_raw(f"/api/admin/foto?ruta={saved['foto']}")
        self.assertEqual((status, body), (200, JPEG))


if __name__ == "__main__":
    unittest.main()
