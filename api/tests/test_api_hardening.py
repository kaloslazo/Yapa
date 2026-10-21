"""Iteración 30: entradas mal formadas en la API (docs/desarrollo/30-auditoria-endurecimiento.md)."""

from datetime import datetime
import unittest
from unittest import mock

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"


class ApiHardeningTests(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.api = create_api(self.store, clock=lambda: WEDNESDAY)

    def client(self, user=101, secret=PIN, kind="vecino"):
        client = ApiClient(self.api)
        client.login(user, secret, kind)
        return client

    def admin(self):
        return self.client(ADMIN, ADMIN_PASS, "admin")

    def assertError(self, response, status, code):
        got_status, data, _ = response
        self.assertEqual((got_status, data["error"]["codigo"]), (status, code))

    # AD-D
    def test_ad_d_un_numero_como_clave_se_lee_como_texto(self):
        client = ApiClient(self.api)
        status, data, _ = client.login(101, 482915)
        self.assertEqual(status, 200)
        self.assertEqual(data["usuario"], 101)

    def test_ad_d_una_lista_como_clave_se_rechaza(self):
        status, data, _ = ApiClient(self.api).login(101, [1])
        self.assertEqual((status, data["error"]["codigo"]), (422, "INVALID_INPUT"))

    def test_ad_d_pin_nuevo_como_numero(self):
        client = self.client()
        status, _, _ = client.post("/api/pin", {"actual": PIN, "nuevo": 135790})
        self.assertEqual(status, 200)
        self.assertEqual(ApiClient(self.api).login(101, "135790")[0], 200)

    def test_ad_d_lista_del_catalogo_como_numero(self):
        self.assertError(self.admin().post("/api/admin/catalogo", {"ciclo": "2026-W41", "lista": 5}),
                         422, "INVALID_CATALOG_FORMAT")

    def test_ad_d_celular_como_numero(self):
        status, data, _ = self.admin().post("/api/admin/vecinos", {"nombre": "Vecino Nuevo", "celular": 999888777,
                                                                    "zona": "Z-LINCE-01", "consentimiento": True,
                                                                    "correo": "vecino.nuevo@correo.pe"})
        self.assertEqual(status, 201)

    def test_ad_d_motivo_como_lista(self):
        self.assertError(self.admin().post("/api/admin/entregas-fallidas",
                                           {"ciclo": "2026-W38", "zona": "Z-LINCE-01", "foto": "x", "motivo": ["x"]}),
                         422, "INVALID_INPUT")

    def test_ad_d_cantidad_enorme_en_la_cotizacion(self):
        self.assertError(self.client().post("/api/cotizar", {"lineas": {"LIMON": "1e999"}}), 422, "INVALID_QUANTITY")

    # AD-E
    def test_ad_e_una_falla_inesperada_responde_json_500(self):
        client = self.client()
        with mock.patch("yapa_sdd.web.api.quote_order", side_effect=RuntimeError("falla de prueba")):
            status, data, headers = client.post("/api/cotizar", {"lineas": {"LIMON": "5"}})
        self.assertEqual((status, data["error"]["codigo"]), (500, "INTERNAL_ERROR"))
        self.assertTrue(headers["Content-Type"].startswith("application/json"))
        self.assertEqual(client.get("/api/sesion")[0], 200)  # el servidor sigue atendiendo

    # AD-F
    def test_ad_f_semana_inexistente_en_las_consultas_del_admin(self):
        admin = self.admin()
        for path in ("/api/admin/resumen", "/api/admin/armado", "/api/admin/metricas"):
            for week in ("2026-W99", "2026-W00"):
                self.assertError(admin.get(f"{path}?ciclo={week}"), 422, "INVALID_CYCLE")


if __name__ == "__main__":
    unittest.main()
