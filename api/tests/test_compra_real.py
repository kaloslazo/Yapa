"""Iteración 56 · Compra real, dañados al armar, rotulado, bloqueo del despacho e incidencias.

Spec: docs/desarrollo/56-compra-real-y-armado.md.
"""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_settlement import BASKET, CYCLE, Scenario
from web_client import fast_hashing

from yapa_sdd import audit, incidents, partners, purchase, wallet
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.buffer import add_to_buffer, buffer_value
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import bag_labels, close_cycle, deliver_zone, pack_bag, register_failed_delivery
from yapa_sdd.web.api import create_api


ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"
PASS = "personal-2026"
BUYER, PACKER, SUPPORT = "compras-1", "armado-1", "atencion-1"
BEFORE_CLOSE = datetime(2026, 9, 16, 19, 59, tzinfo=LIMA)
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
LINES = BASKET + [("LIMPIATODO-GALON", "2")]


class Base(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8, lines=LINES)
        for user, kind in ((BUYER, partners.BUYER), (PACKER, partners.PACKER), (SUPPORT, partners.SUPPORT)):
            partners.create_staff(self.store, user, kind, "Persona", PASS, by=ADMIN, now=FRIDAY)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def buy(self, received=None, by=BUYER, now=FRIDAY):
        return purchase.register_purchase(self.store, CYCLE, received or {}, by=by, now=now)

    def damaged(self, order_id=3, product_id="CEBOLLA-ROJA", quantity="1", photo="fotos/danado.jpg", by=PACKER):
        return purchase.register_damaged(self.store, order_id, product_id, quantity, by=by, photo=photo, now=FRIDAY)

    def pack_all(self):
        for order in self.orders:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)

    def deliver(self):
        return deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/entrega.jpg",
                            received_by="Sr. Ramos", now=SATURDAY)

    def close(self):
        self.pack_all()
        self.deliver()
        return close_cycle(self.store, CYCLE, at=SATURDAY)

    def missing(self, result, order_id, product_id):
        return next(line.missing for line in result.orders[order_id].lines if line.product_id == product_id)


class PurchaseSpecTests(Base):
    # CR-A
    def test_cr_a_shortage_goes_to_the_last_order(self):
        self.buy({"PAPA-AMARILLA": "36"})
        result = self.close()
        self.assertEqual(self.missing(result, 8, "PAPA-AMARILLA"), D("4"))
        for order_id in range(1, 8):
            self.assertEqual(self.missing(result, order_id, "PAPA-AMARILLA"), D("0"))
        self.assertEqual(result.products["PAPA-AMARILLA"].total_quantity, D("40"))  # LQ-03 sigue con lo pedido
        full = result.orders[7].final_amount - result.orders[8].final_amount
        price = result.products["PAPA-AMARILLA"].final_unit_price
        self.assertLessEqual(abs(full - 4 * price), D("0.01"))  # le vuelven los 4 kg al precio final

    # CR-B
    def test_cr_b_shortage_spills_to_the_previous_order(self):
        self.buy({"PAPA-AMARILLA": "33"})
        result = self.close()
        self.assertEqual(self.missing(result, 8, "PAPA-AMARILLA"), D("5"))
        self.assertEqual(self.missing(result, 7, "PAPA-AMARILLA"), D("2"))
        self.assertEqual(self.missing(result, 6, "PAPA-AMARILLA"), D("0"))

    # CR-C
    def test_cr_c_buffer_covers_first(self):
        add_to_buffer(self.store, CYCLE, "LIMPIATODO-GALON", "3", by=BUYER)
        self.buy({"LIMPIATODO-GALON": "12"})
        self.assertEqual(self.store.buffer["LIMPIATODO-GALON"].quantity, D("0"))
        uses = [(u.order_id, u.quantity) for u in self.store.buffer_uses]
        self.assertEqual(uses, [(8, D("2")), (7, D("1"))])
        result = self.close()
        self.assertEqual(self.missing(result, 8, "LIMPIATODO-GALON"), D("0"))
        self.assertEqual(self.missing(result, 7, "LIMPIATODO-GALON"), D("1"))

    # CR-D
    def test_cr_d_invalid_items(self):
        for received in ({"PAPA-AMARILLA": "41"}, {"PAPA-AMARILLA": "-1"}, {"PAPA-AMARILLA": "1.5"},
                         {"PAPA-AMARILLA": "abc"}, {"LIMON": "0"}):
            self.assertRule("INVALID_PURCHASE_ITEM", self.buy, received)
        self.assertEqual(self.store.purchases, {})

    def test_cr_d_before_close_and_roles(self):
        self.assertRule("CYCLE_STILL_OPEN", self.buy, now=BEFORE_CLOSE)
        self.assertRule("NOT_AUTHORIZED", self.buy, by=PACKER)
        self.assertRule("NOT_AUTHORIZED", self.buy, by=101)
        self.buy(by=ADMIN)
        self.assertRule("PURCHASE_ALREADY_REGISTERED", self.buy)

    # CR-E
    def test_cr_e_full_purchase_changes_nothing(self):
        self.buy()
        result = self.close()
        for settled in result.orders.values():
            self.assertTrue(all(line.missing == 0 for line in settled.lines))
        self.assertEqual(audit.money_balance(self.store).difference, D("0"))


class DamagedSpecTests(Base):
    # DA-A
    def test_da_a_damaged_is_returned_in_settlement(self):
        self.buy()
        self.damaged()
        result = self.close()
        self.assertEqual(self.missing(result, 3, "CEBOLLA-ROJA"), D("1"))
        self.assertEqual(self.missing(result, 4, "CEBOLLA-ROJA"), D("0"))

    # DA-B
    def test_da_b_buffer_replaces_damaged(self):
        add_to_buffer(self.store, CYCLE, "LIMPIATODO-GALON", "2", by=BUYER)
        self.buy()
        self.damaged(product_id="LIMPIATODO-GALON")
        self.assertEqual(self.store.buffer["LIMPIATODO-GALON"].quantity, D("1"))
        result = self.close()
        self.assertEqual(self.missing(result, 3, "LIMPIATODO-GALON"), D("0"))

    # DA-C
    def test_da_c_limits(self):
        self.assertRule("PURCHASE_NOT_REGISTERED", self.damaged)
        self.buy()
        for quantity, product in (("0", "CEBOLLA-ROJA"), ("1.5", "CEBOLLA-ROJA"), ("1", "LIMON")):
            self.assertRule("INVALID_DAMAGED_ITEM", self.damaged, quantity=quantity, product_id=product)
        self.damaged()
        self.assertRule("INVALID_DAMAGED_ITEM", self.damaged, quantity="10")
        self.assertRule("PHOTO_REQUIRED", self.damaged, photo="  ")
        self.assertRule("NOT_AUTHORIZED", self.damaged, by=BUYER)
        self.assertRule("NOT_AUTHORIZED", self.damaged, by=SUPPORT)
        self.assertRule("ORDER_NOT_FOUND", self.damaged, order_id=999)
        self.pack_all()
        self.deliver()
        self.assertRule("ZONE_ALREADY_CLOSED", self.damaged)

    def test_da_c_shortage_and_damaged_add_up(self):
        self.buy({"PAPA-AMARILLA": "36"})  # el pedido 8 ya perdió 4 kg
        self.assertRule("INVALID_DAMAGED_ITEM", self.damaged, order_id=8, product_id="PAPA-AMARILLA", quantity="2")
        self.damaged(order_id=8, product_id="PAPA-AMARILLA", quantity="1")


class LabelsAndDispatchTests(Base):
    # RT-A
    def test_rt_a_labels(self):
        for _ in range(2):
            pack_bag(self.store, 1, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)
        self.assertEqual(bag_labels(self.store, 1), ["Pedido 1 · Residencial San Felipe · Bolsa 1 de 2",
                                                      "Pedido 1 · Residencial San Felipe · Bolsa 2 de 2"])

    # BD-A
    def test_bd_a_dispatch_waits_for_purchase(self):
        self.pack_all()
        self.assertRule("PURCHASE_NOT_REGISTERED", self.deliver)
        self.assertRule("PURCHASE_NOT_REGISTERED", register_failed_delivery, self.store, CYCLE, "Z-JM-01", by=ADMIN,
                        photo="fotos/puerta.jpg", reason="PORTERIA_CERRADA", now=SATURDAY)
        self.buy()
        self.assertEqual(len(self.deliver().order_ids), 8)


class IncidentSpecTests(Base):
    def open(self, order_id=2, kind="ENTREGA", text="La portería dice que llegó tarde", by=SUPPORT):
        return incidents.open_incident(self.store, order_id, kind, text, by=by, now=FRIDAY)

    # IN-A
    def test_in_a_open_and_close(self):
        before = wallet.balance(self.store, self.orders[1].customer_id)
        incident = self.open()
        self.assertEqual(incident.status, "ABIERTA")
        closed = incidents.close_incident(self.store, incident.incident_id, "Se habló con el vecino", by=SUPPORT,
                                          now=SATURDAY)
        self.assertEqual((closed.status, closed.note), ("CERRADA", "Se habló con el vecino"))
        self.assertEqual(wallet.balance(self.store, self.orders[1].customer_id), before)
        self.assertEqual(audit.money_balance(self.store).difference, D("0"))

    # IN-B
    def test_in_b_invalid(self):
        self.assertRule("INVALID_INCIDENT", self.open, kind="QUEJA")
        self.assertRule("INVALID_INCIDENT", self.open, text="  ")
        self.assertRule("INVALID_INCIDENT", self.open, text="x" * 501)
        self.assertRule("ORDER_NOT_FOUND", self.open, order_id=999)
        self.assertRule("NOT_AUTHORIZED", self.open, by=PACKER)
        incident = self.open(by=ADMIN)
        close = incidents.close_incident
        self.assertRule("INVALID_INCIDENT", close, self.store, incident.incident_id, " ", by=SUPPORT, now=FRIDAY)
        close(self.store, incident.incident_id, "Listo", by=SUPPORT, now=FRIDAY)
        self.assertRule("INCIDENT_ALREADY_CLOSED", close, self.store, incident.incident_id, "Otra", by=SUPPORT, now=FRIDAY)
        self.assertRule("INCIDENT_NOT_FOUND", close, self.store, 999, "Nota", by=SUPPORT, now=FRIDAY)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        set_pin(self.store, 101, PIN)
        self.now = FRIDAY
        self.api = create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY)
        self.admin = ApiClient(self.api)
        self.assertEqual(self.admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)

    def client(self, user, kind):
        client = ApiClient(self.api)
        self.assertEqual(client.login(user, PASS, kind)[0], 200)
        return client

    # API-A
    def test_api_a_purchase_damaged_labels_and_incidents(self):
        buyer, packer, support = self.client(BUYER, "compras"), self.client(PACKER, "armador"), self.client(SUPPORT, "atencion")
        status, data, _ = buyer.get(f"/api/compras?ciclo={CYCLE}")
        self.assertEqual((status, data["compra_real"]), (200, None))
        self.assertEqual(packer.post("/api/compras/recibido", {"ciclo": CYCLE, "recibido": {}})[0], 403)
        status, data, _ = buyer.post("/api/compras/recibido", {"ciclo": CYCLE, "recibido": {"PAPA-AMARILLA": "36"}})
        self.assertEqual(status, 200)
        status, data, _ = buyer.get(f"/api/compras?ciclo={CYCLE}")
        self.assertEqual(data["compra_real"]["faltantes"],
                         [{"pedido": 8, "producto": "PAPA-AMARILLA", "cantidad": "4", "colchon": "0", "origen": "COMPRA",
                           "nombre": "Papa amarilla"}])  # OC-03 (iteración 64)

        self.assertEqual(buyer.post("/api/admin/danados", {"pedido": 3, "producto": "CEBOLLA-ROJA", "cantidad": "1",
                                                            "foto": "fotos/d.jpg"})[0], 403)
        status, data, _ = packer.post("/api/admin/danados", {"pedido": 3, "producto": "CEBOLLA-ROJA", "cantidad": "1",
                                                              "foto": "fotos/d.jpg"})
        self.assertEqual((status, data["origen"]), (200, "DANADO"))

        packer.post("/api/admin/bolsas", {"pedido": 1, "foto": "fotos/b.jpg"})
        status, data, _ = packer.get(f"/api/admin/armado?ciclo={CYCLE}")
        first = next(o for o in data["pedidos"] if o["id"] == 1)
        self.assertEqual(first["rotulos"], ["Pedido 1 · Residencial San Felipe · Bolsa 1 de 1"])

        self.assertEqual(packer.get("/api/admin/incidencias")[0], 403)
        status, data, _ = support.post("/api/admin/incidencias", {"pedido": 2, "tipo": "BOLSA", "descripcion": "Bolsa rota"})
        self.assertEqual((status, data["estado"]), (200, "ABIERTA"))
        status, data, _ = support.post(f"/api/admin/incidencias/{data['id']}/cerrar", {"nota": "Se repuso"})
        self.assertEqual((status, data["estado"]), (200, "CERRADA"))
        status, data, _ = self.admin.get("/api/admin/incidencias")
        self.assertEqual((status, len(data["incidencias"])), (200, 1))


if __name__ == "__main__":
    unittest.main()
