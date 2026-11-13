"""Iteración 67 · Cantidades con su unidad. Spec: docs/desarrollo/67-cantidades-con-unidad.md."""

from datetime import timedelta

from api_client import ApiClient
from test_personal_por_rol import ADMIN, ADMIN_PASS, FRIDAY, PASS, PIN, SATURDAY, Base
from test_settlement import CYCLE

from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.web.api import create_api


class UnitTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.now = FRIDAY
        self.api = create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY)
        self.admin = ApiClient(self.api)
        self.assertEqual(self.admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)

    # UN-A
    def test_un_a_order_lines_carry_the_unit(self):
        status, data, _ = self.admin.get(f"/api/admin/resumen?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertEqual({l["unidad"] for l in data["pedidos"][0]["lineas"]}, {"kg"})

    # UN-B
    def test_un_b_the_packer_gets_the_unit(self):
        self.admin.post("/api/admin/cuentas", {"tipo": "armador", "usuario": "armado-1", "nombre": "Rosa", "contrasena": PASS})
        packer = ApiClient(self.api)
        self.assertEqual(packer.login("armado-1", PASS, "armador")[0], 200)
        status, data, _ = packer.get(f"/api/admin/armado?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertEqual(set(data["pedidos"][0]["lineas"][0]), {"id", "nombre", "cantidad", "unidad"})

    # UN-C
    def test_un_c_claim_options_carry_the_unit(self):
        self.deliver()
        set_pin(self.store, self.first.customer_id, PIN)
        self.now = SATURDAY + timedelta(hours=1)
        neighbor = ApiClient(self.api)
        self.assertEqual(neighbor.login(self.first.customer_id, PIN)[0], 200)
        status, data, _ = neighbor.get("/api/reclamos")
        self.assertEqual(status, 200)
        self.assertEqual({o["unidad"] for o in data["reclamables"]}, {"kg"})
