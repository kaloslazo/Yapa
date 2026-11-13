"""Iteración 64 · La operación en el celular. Spec: docs/desarrollo/64-operacion-en-el-celular.md."""

from datetime import timedelta

from api_client import ApiClient
from test_personal_por_rol import ADMIN, ADMIN_PASS, FRIDAY, PASS, SATURDAY, Base
from test_settlement import CYCLE

from yapa_sdd.auth import set_admin_password
from yapa_sdd.buffer import add_to_buffer
from yapa_sdd.claims import file_claim
from yapa_sdd.purchase import register_purchase
from yapa_sdd.web.api import create_api


class OperationOnPhoneTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.now = FRIDAY
        self.api = create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY)
        self.admin = ApiClient(self.api)
        self.assertEqual(self.admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)

    def client(self, user, kind):
        status, _, _ = self.admin.post("/api/admin/cuentas", {"tipo": kind, "usuario": user, "nombre": "Persona",
                                                              "contrasena": PASS})
        self.assertEqual(status, 201)
        client = ApiClient(self.api)
        self.assertEqual(client.login(user, PASS, kind)[0], 200)
        return client

    # OC-A
    def test_oc_a_support_lists_the_week_orders_without_money(self):
        support = self.client("atencion-1", "atencion")
        status, data, _ = support.get(f"/api/admin/pedidos?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertEqual(data["ciclo"], CYCLE)
        self.assertIn(CYCLE, data["ciclos"])
        self.assertEqual(len(data["pedidos"]), 8)
        first = data["pedidos"][0]
        self.assertEqual(set(first), {"id", "vecino", "zona", "estado"})
        self.assertEqual(first["zona"], "Residencial San Felipe")
        self.assertEqual(first["vecino"], self.store.customers[self.first.customer_id].name)

    def test_oc_a_admin_too_but_not_the_packer(self):
        self.assertEqual(self.admin.get(f"/api/admin/pedidos?ciclo={CYCLE}")[0], 200)
        packer = self.client("armado-1", "armador")
        status, data, _ = packer.get(f"/api/admin/pedidos?ciclo={CYCLE}")
        self.assertEqual((status, data["error"]["codigo"]), (403, "FORBIDDEN"))

    # OC-B
    def test_oc_b_claims_shortages_and_buffer_carry_the_product_name(self):
        self.deliver()
        file_claim(self.store, self.first.order_id, customer_id=self.first.customer_id, product_id="CEBOLLA-ROJA",
                   quantity="1", reason="DANADO", photo="fotos/reclamo.jpg", now=SATURDAY + timedelta(hours=1))
        self.now = SATURDAY + timedelta(hours=2)
        status, data, _ = self.admin.get("/api/admin/reclamos")
        self.assertEqual(status, 200)
        self.assertEqual(data["reclamos"][0]["nombre"], "Cebolla roja")

    def test_oc_b_shortage_and_buffer_names(self):
        register_purchase(self.store, CYCLE, {"PAPA-AMARILLA": "36"}, by=ADMIN, now=FRIDAY)
        add_to_buffer(self.store, CYCLE, "LIMPIATODO-GALON", "2", by=ADMIN)
        status, data, _ = self.admin.get(f"/api/compras?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertEqual({f["nombre"] for f in data["compra_real"]["faltantes"]}, {"Papa amarilla"})
        self.assertEqual(data["colchon"]["stock"][0]["nombre"], "Limpiatodo galón 3.8 L")

    # OC-C
    def test_oc_c_buffer_choices_are_the_cleaning_products(self):
        status, data, _ = self.admin.get(f"/api/compras?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        ids = {p["id"] for p in data["guardables"]}
        self.assertIn("LIMPIATODO-GALON", ids)
        self.assertIn("DETERGENTE-LIQUIDO-GALON", ids)
        self.assertNotIn("PAPA-AMARILLA", ids)
        self.assertTrue(all(set(p) == {"id", "nombre", "unidad"} for p in data["guardables"]))

    # OC-D
    def test_oc_d_orders_carry_the_building_name(self):
        status, data, _ = self.admin.get(f"/api/admin/resumen?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertEqual(data["pedidos"][0]["zona_nombre"], "Residencial San Felipe")
        status, data, _ = self.admin.get(f"/api/admin/armado?ciclo={CYCLE}")
        self.assertEqual(data["pedidos"][0]["zona_nombre"], "Residencial San Felipe")
