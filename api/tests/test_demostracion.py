"""Iteración 48 · Datos de demostración y cuentas de depuración. Spec: docs/desarrollo/48-demostracion-y-depuracion.md."""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from api_client import ApiClient
from web_client import fast_hashing

from yapa_sdd import audit, auth, cycle, persistence
from yapa_sdd.auth import MAX_FAILURES, set_admin_password
from yapa_sdd.cycle import LIMA
from yapa_sdd.demo import DEMO_NOW, demo_clock, demo_store, seed_demo_base
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.web.api import create_api

NOW = datetime(2026, 10, 21, 10, 0, tzinfo=LIMA)  # miércoles de la semana 43
PINS = {101: "428193", 105: "739104", 116: "260318"}
DEBUG = "clave-depuracion-2026"
TEAM = ("admin-yapa", "clave-del-equipo-2026")


class DemoBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = str(Path(self.dir.name) / "demo.db")

    def seed(self, pins=PINS, debug=DEBUG):
        store = seed_demo_base(self.path, NOW, pins, debug)
        set_admin_password(store, *TEAM)
        return store

    def code_of(self, response):
        return response[1]["error"]["codigo"]


class DemoDataTests(DemoBase):
    # DM-A
    def test_dm_a_sin_now_queda_como_antes(self):
        store = demo_store()
        self.assertTrue(store.orders_in_cycle("2026-W39"))
        self.assertTrue(store.orders_in_cycle("2026-W40"))
        self.assertFalse(store.orders_in_cycle("2026-W43"))

    # DM-B
    def test_dm_b_corrida_a_la_semana_actual(self):
        store = demo_store(now=NOW)
        self.assertTrue(store.orders_in_cycle("2026-W42"))
        self.assertTrue(store.orders_in_cycle("2026-W43"))
        self.assertFalse(store.orders_in_cycle("2026-W39"))
        self.assertTrue(cycle.is_open(NOW))
        self.assertEqual(cycle.cycle_id(NOW), "2026-W43")
        self.assertIn("2026-W42", store.settlements)  # la anterior, liquidada
        self.assertNotIn("2026-W43", store.settlements)  # la actual sigue abierta
        self.assertEqual(audit.money_balance(store).difference, 0)

    def test_dm_b_otra_semana_cualquiera(self):
        later = datetime(2027, 1, 6, 10, 0, tzinfo=LIMA)  # cruza el año
        store = demo_store(now=later)
        self.assertEqual(cycle.cycle_id(later), "2027-W01")
        self.assertTrue(store.orders_in_cycle("2026-W53"))
        self.assertTrue(store.orders_in_cycle("2027-W01"))
        self.assertEqual(audit.money_balance(store).difference, 0)

    # DM-C
    def test_dm_c_cuentas_y_roles(self):
        store = self.seed()
        self.assertEqual(store.zones["Z-LINCE-01"].admin_id, 101)
        self.assertEqual(store.zones["Z-LINCE-03"].admin_id, 116)
        self.assertFalse(any(z.admin_id == 105 for z in store.zones.values()))
        now = datetime.now(LIMA)
        for customer, pin in PINS.items():
            self.assertEqual(auth.authenticate(store, "vecino", customer, pin, now), customer)
        self.assertEqual(auth.authenticate(store, "admin", *TEAM, now), "admin-yapa")
        self.assertEqual(auth.authenticate(store, "admin", "debug-global", DEBUG, now), "debug-global")
        self.assertNotIn(("vecino", "106"), store.credentials)  # los demás vecinos no tienen PIN conocido

    # DM-D
    def test_dm_d_pin_faltante_o_flojo(self):
        for pins, code in (({101: "428193", 105: "739104"}, "DEMO_PINS_REQUIRED"), ({**PINS, 116: "123456"}, "INVALID_PIN")):
            with self.assertRaises(BusinessRuleError) as raised:
                seed_demo_base(self.path, NOW, pins, DEBUG)
            self.assertEqual(raised.exception.code, code)
        with self.assertRaises(BusinessRuleError) as raised:
            seed_demo_base(self.path, NOW, PINS, "corta")
        self.assertEqual(raised.exception.code, "INVALID_PASSWORD")
        self.assertFalse(Path(self.path).exists())

    # DM-E
    def test_dm_e_se_guarda_y_se_recarga(self):
        self.seed()
        loaded = persistence.open_store(self.path)
        self.assertEqual(demo_clock(loaded), NOW)
        self.assertEqual(loaded.zones["Z-LINCE-01"].admin_id, 101)
        self.assertEqual(auth.authenticate(loaded, "vecino", 101, PINS[101], datetime.now(LIMA)), 101)
        self.assertIsNone(demo_clock(persistence.open_store(str(Path(self.dir.name) / "limpia.db"))))  # sin demo: nada

    def test_dm_e_no_pisa_una_base_que_ya_existe(self):
        self.seed()
        with self.assertRaises(BusinessRuleError) as raised:
            seed_demo_base(self.path, NOW, PINS, DEBUG)
        self.assertEqual(raised.exception.code, "DATABASE_EXISTS")


class SecurityClockTests(DemoBase):
    # DM-F
    def test_dm_f_la_seguridad_usa_la_hora_real(self):
        store = self.seed()
        real = [datetime(2026, 10, 25, 12, 0, tzinfo=LIMA)]
        api = create_api(store, clock=lambda: NOW, security_clock=lambda: real[0])
        for _ in range(MAX_FAILURES):
            ApiClient(api).login(105, "000000")
        self.assertEqual(self.code_of(ApiClient(api).login(105, PINS[105])), "ACCOUNT_LOCKED")
        real[0] += timedelta(minutes=16)
        self.assertEqual(ApiClient(api).login(105, PINS[105])[0], 200)

    def test_dm_f_la_sesion_vence_con_la_hora_real(self):
        store = self.seed()
        real = [datetime(2026, 10, 25, 12, 0, tzinfo=LIMA)]
        api = create_api(store, clock=lambda: NOW, security_clock=lambda: real[0])
        client = ApiClient(api)
        client.login(105, PINS[105])
        self.assertEqual(client.get("/api/sesion")[0], 200)
        real[0] += timedelta(hours=9)
        self.assertEqual(client.get("/api/sesion")[0], 401)

    def test_dm_f_sin_security_clock_todo_sigue_igual(self):
        store = self.seed()
        clock = [NOW]
        api = create_api(store, clock=lambda: clock[0])
        for _ in range(MAX_FAILURES):
            ApiClient(api).login(105, "000000")
        clock[0] += timedelta(minutes=16)
        self.assertEqual(ApiClient(api).login(105, PINS[105])[0], 200)


class ViewAsTests(DemoBase):
    def setUp(self):
        super().setUp()
        self.store = self.seed()
        self.api = create_api(self.store, clock=lambda: NOW)

    def debug(self):
        client = ApiClient(self.api)
        self.assertEqual(client.login("debug-global", DEBUG, "admin")[0], 200)
        return client

    # DM-G
    def test_dm_g_ver_como(self):
        client = self.debug()
        status, body, _ = client.post("/api/admin/ver-como", {"usuario": 101})
        self.assertEqual(status, 200, body)
        status, me, _ = client.get("/api/sesion")
        self.assertEqual((me["usuario"], me["rol"]), (101, "admin_zona"))
        self.assertEqual(me["viendo_como"], {"admin": "debug-global"})
        self.assertEqual(client.get("/api/mi-zona")[0], 200)  # ve la pantalla de Ana
        self.assertEqual(client.get("/api/admin/vecinos")[0], 403)  # y no el panel del equipo

    def test_dm_g_ver_como_una_vecina(self):
        client = self.debug()
        client.post("/api/admin/ver-como", {"usuario": "105"})
        self.assertEqual(client.get("/api/sesion")[1]["rol"], "vecino")

    def test_dm_g_solo_el_admin_global(self):
        normal = ApiClient(self.api)
        normal.login(*TEAM, "admin")
        self.assertEqual(self.code_of(normal.post("/api/admin/ver-como", {"usuario": 101})), "NOT_DEBUG_ADMIN")
        neighbor = ApiClient(self.api)
        neighbor.login(101, PINS[101])
        self.assertEqual(neighbor.post("/api/admin/ver-como", {"usuario": 105})[0], 403)
        self.assertEqual(ApiClient(self.api).post("/api/admin/ver-como", {"usuario": 105}, with_csrf=False)[0], 401)

    def test_dm_g_no_se_hace_pasar_por_otro_admin(self):
        client = self.debug()
        self.assertEqual(self.code_of(client.post("/api/admin/ver-como", {"usuario": "admin-yapa"})), "CUSTOMER_NOT_FOUND")

    # DM-H
    def test_dm_h_volver(self):
        client = self.debug()
        self.assertEqual(self.code_of(client.post("/api/sesion/volver")), "NOT_VIEWING_AS")
        client.post("/api/admin/ver-como", {"usuario": 101})
        status, body, _ = client.post("/api/sesion/volver")
        self.assertEqual(status, 200, body)
        me = client.get("/api/sesion")[1]
        self.assertEqual((me["usuario"], me["rol"]), ("debug-global", "admin"))
        self.assertNotIn("viendo_como", me)

    # DM-I
    def test_dm_i_credenciales_bloqueadas(self):
        client = self.debug()
        client.post("/api/admin/ver-como", {"usuario": 101})
        before = (self.store.customers[101], dict(self.store.credentials))
        for path, body in (("/api/pin", {"actual": PINS[101], "nuevo": "835921"}), ("/api/pin/crear", {"pin": "835921"}),
                           ("/api/cuenta/correo", {"correo": "otro@correo.pe"}),
                           ("/api/cuenta/correo/verificar", {"codigo": "123456"}),
                           ("/api/cuenta/google", {"credential": "x"}), ("/api/cuenta/google/desvincular", {})):
            response = client.post(path, body)
            self.assertEqual((response[0], self.code_of(response)), (422, "DEBUG_SESSION_READONLY"), path)
        self.assertEqual(before, (self.store.customers[101], dict(self.store.credentials)))

    def test_dm_i_lo_del_negocio_si_se_puede(self):
        client = self.debug()
        client.post("/api/admin/ver-como", {"usuario": 105})
        self.assertEqual(client.get("/api/mis-pedidos")[0], 200)
        self.assertEqual(client.get("/api/avisos")[0], 200)

    # DM-J
    def test_dm_j_registro(self):
        client = self.debug()
        client.post("/api/admin/ver-como", {"usuario": 101})
        client.post("/api/sesion/volver")
        log = self.store.debug_log
        self.assertEqual([entry["accion"] for entry in log], ["ver-como", "volver"])
        self.assertEqual((log[0]["admin"], log[0]["como"]), ("debug-global", 101))
        self.assertIsInstance(log[0]["momento"], datetime)
        self.assertEqual(json.loads(json.dumps(log[0]["admin"])), "debug-global")

    # DM-K
    def test_dm_k_quien_no_existe(self):
        client = self.debug()
        self.assertEqual(self.code_of(client.post("/api/admin/ver-como", {"usuario": 99999})), "CUSTOMER_NOT_FOUND")
        self.assertEqual(client.get("/api/sesion")[1]["usuario"], "debug-global")
        self.assertEqual(self.store.debug_log, [])

    def test_el_registro_sobrevive_a_guardar_y_cargar(self):
        client = self.debug()
        client.post("/api/admin/ver-como", {"usuario": 101})
        persistence.save(self.store, self.path + ".2")
        self.assertEqual(len(persistence.load(self.path + ".2").debug_log), 1)


if __name__ == "__main__":
    unittest.main()
