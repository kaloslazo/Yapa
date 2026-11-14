"""Iteración 65 · Los pedidos y los reclamos del vecino, como un carrito. Spec: docs/desarrollo/65-reclamos-como-un-carrito.md."""

from datetime import timedelta

from api_client import ApiClient
from test_personal_por_rol import FRIDAY, PIN, SATURDAY, Base

from yapa_sdd.auth import set_pin
from yapa_sdd.claims import file_claim
from yapa_sdd.web.api import create_api


class ClaimOptionsTests(Base):
    def setUp(self):
        super().setUp()
        self.deliver()  # entregado el sábado 19/09 a las 10:00
        set_pin(self.store, self.first.customer_id, PIN)
        self.now = SATURDAY + timedelta(hours=1)
        self.api = create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY)
        self.neighbor = ApiClient(self.api)
        self.assertEqual(self.neighbor.login(self.first.customer_id, PIN)[0], 200)

    # RV-A
    def test_rv_a_within_24_hours_every_product_with_its_deadline(self):
        status, data, _ = self.neighbor.get("/api/reclamos")
        self.assertEqual(status, 200)
        mine = [o for o in data["reclamables"] if o["pedido"] == self.first.order_id]
        self.assertEqual({o["producto"] for o in mine}, {"PAPA-AMARILLA", "PAPA-BLANCA", "CEBOLLA-ROJA"})
        self.assertTrue(all(o["hasta"] == "2026-09-20T10:00:00-05:00" for o in mine))

    # RV-B
    def test_rv_b_after_24_hours_no_options_but_claims_keep_their_name(self):
        file_claim(self.store, self.first.order_id, customer_id=self.first.customer_id, product_id="CEBOLLA-ROJA",
                   quantity="1", reason="DANADO", photo="fotos/reclamo.jpg", now=self.now)
        self.now = SATURDAY + timedelta(hours=24)
        status, data, _ = self.neighbor.get("/api/reclamos")
        self.assertEqual(status, 200)
        self.assertEqual(data["reclamables"], [])
        self.assertEqual(data["reclamos"][0]["nombre"], "Cebolla roja")
