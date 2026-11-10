"""Iteración 59 · Seguimiento del pedido. Spec: docs/desarrollo/59-seguimiento-del-pedido.md."""

from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from api_client import ApiClient
from test_settlement import BASKET, CYCLE, NOW, Scenario, buy_all
from web_client import fast_hashing

from yapa_sdd import logistics, partners, purchase, reception
from yapa_sdd.auth import set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.fulfillment import close_cycle, deliver_zone, pack_bag
from yapa_sdd.order_changes import cancel_order
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.api import create_api


ADMIN, PIN = "admin-yapa", "482915"
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
FOTO_BOLSA, FOTO_ENTREGA = "fotos/0123456789abcdef.jpg", "fotos/fedcba9876543210.jpg"


class Base(unittest.TestCase):
    def setUp(self):
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)
        self.first = self.orders[0]

    def steps(self, order=None):
        return {p["paso"]: p for p in logistics.tracking(self.store, order or self.first)}

    def status(self, order=None):
        return logistics.order_status(self.store, order or self.first)

    def pack_all(self, bags=1):
        for order in self.orders:
            for _ in range(bags):
                pack_bag(self.store, order.order_id, by=ADMIN, photo=FOTO_BOLSA, now=FRIDAY)

    def deliver(self):
        return deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo=FOTO_ENTREGA, received_by="Sr. Ramos",
                            now=SATURDAY)


class TrackingSpecTests(Base):
    # SG-A
    def test_sg_a_pending_payment(self):
        order = self.s.order("Z-JM-01", verified=False)
        self.assertEqual(self.status(order)["titulo"], "Falta tu pago")
        steps = self.steps(order)
        self.assertEqual(steps["Pedido"]["cuando"], NOW.isoformat())
        self.assertFalse(steps["Pago verificado"]["hecho"])

    # SG-B
    def test_sg_b_verified(self):
        status = self.status()
        self.assertEqual((status["titulo"], status["detalle"]),
                         ("Pago verificado", "Compramos el jueves y entregamos el sábado 19/09."))
        paso = self.steps()["Pago verificado"]
        self.assertEqual((paso["cuando"], paso["detalle"]), (NOW.isoformat(), "Yape · S/ 61.00"))

    # SG-C
    def test_sg_c_bought_with_shortage(self):
        purchase.register_purchase(self.store, CYCLE, {"PAPA-AMARILLA": "36"}, by=ADMIN, now=FRIDAY)
        self.assertEqual(self.steps(self.orders[7])["Comprado"]["detalle"], "Faltó 4 kg de Papa amarilla: vuelve como saldo")
        self.assertEqual(self.steps()["Comprado"]["detalle"], "Llegó todo")
        self.assertEqual(self.steps()["Comprado"]["cuando"], FRIDAY.isoformat())
        self.assertEqual(self.status()["titulo"], "Comprado")

    # SG-D
    def test_sg_d_packed_and_on_the_way(self):
        buy_all(self.store)
        self.pack_all(bags=2)
        self.assertEqual(self.steps()["Armado"]["detalle"], "2 bolsas, con foto")
        self.assertEqual(self.status()["titulo"], "Armado")
        logistics.dispatch_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, now=SATURDAY)
        self.assertEqual(self.status()["titulo"], "En camino a Residencial San Felipe")
        self.assertEqual(self.steps()["En camino"]["cuando"], SATURDAY.isoformat())

    # SG-E
    def test_sg_e_delivered_and_received(self):
        buy_all(self.store)
        self.pack_all(bags=2)
        self.deliver()
        partners.create_staff(self.store, "porteria-jm", partners.CONCIERGE, "Portería", "personal-2026", by=ADMIN,
                              now=FRIDAY, zone_id="Z-JM-01")
        reception.confirm_reception(self.store, CYCLE, "Z-JM-01", by="porteria-jm", now=SATURDAY)
        self.assertEqual(self.status()["titulo"], "Entregado en Residencial San Felipe")
        detalle = self.steps()["Entregado"]["detalle"]
        self.assertIn("Lo recibió Sr. Ramos", detalle)
        self.assertIn("La portería lo confirmó", detalle)
        self.assertEqual(logistics.order_photos(self.store, self.first), {"entrega": FOTO_ENTREGA,
                                                                          "bolsas": [FOTO_BOLSA, FOTO_BOLSA]})

    # SG-F
    def test_sg_f_settled(self):
        buy_all(self.store)
        self.pack_all()
        self.deliver()
        result = close_cycle(self.store, CYCLE, at=SATURDAY)
        returned = result.orders[self.first.order_id].refund_amount
        self.assertEqual(self.status()["titulo"], f"Te devolvimos S/ {returned:.2f}")
        self.assertTrue(self.steps()["Te devolvemos"]["hecho"])

    # SG-G
    def test_sg_g_final_states(self):
        cancelled = self.s.order("Z-JM-01")
        cancel_order(self.store, cancelled.order_id, customer_id=cancelled.customer_id, now=NOW, refund_to="SALDO")
        self.assertEqual(self.status(cancelled)["titulo"], "Cancelaste este pedido")
        unpaid = self.s.order("Z-JM-01", verified=False)
        lonely = self.s.order("Z-LINCE-01")
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        self.assertEqual(self.status(unpaid)["titulo"], "Anulado: el pago no llegó antes del cierre")
        self.assertEqual(self.status(lonely)["titulo"], "Tu grupo no llegó a 8 pedidos")


class PhotoApiTests(Base):
    # SG-H
    def test_sg_h_owner_sees_own_photos(self):
        fast_hashing(self)
        buy_all(self.store)
        self.pack_all()
        self.deliver()
        carpeta = tempfile.mkdtemp()
        (Path(carpeta) / "0123456789abcdef.jpg").write_bytes(b"bolsa")
        (Path(carpeta) / "fedcba9876543210.jpg").write_bytes(b"entrega")
        set_pin(self.store, self.first.customer_id, PIN)
        set_pin(self.store, self.orders[1].customer_id, PIN)
        api = create_api(self.store, clock=lambda: SATURDAY, photo_dir=carpeta)
        owner, other = ApiClient(api), ApiClient(api)
        self.assertEqual(owner.login(self.first.customer_id, PIN)[0], 200)
        self.assertEqual(other.login(self.orders[1].customer_id, PIN)[0], 200)
        oid = self.first.order_id
        status, body, _ = owner.get_raw(f"/api/pedidos/{oid}/fotos/entrega")
        self.assertEqual((status, body), (200, b"entrega"))
        self.assertEqual(owner.get_raw(f"/api/pedidos/{oid}/fotos/bolsa-1")[:2], (200, b"bolsa"))
        self.assertEqual(other.get_raw(f"/api/pedidos/{oid}/fotos/entrega")[0], 404)
        self.assertEqual(owner.get_raw(f"/api/pedidos/{oid}/fotos/bolsa-9")[0], 404)
        self.assertEqual(owner.get_raw(f"/api/pedidos/{oid}/fotos/cualquiera")[0], 404)
        status, data, _ = owner.get("/api/mis-pedidos")
        mine = next(p for p in data["pedidos"] if p["id"] == oid)
        self.assertEqual(mine["fotos"], {"entrega": True, "bolsas": 1})
        self.assertEqual(mine["estado_seguimiento"]["titulo"], "Entregado en Residencial San Felipe")
        self.assertEqual(len(mine["seguimiento"]), 7)


if __name__ == "__main__":
    unittest.main()
