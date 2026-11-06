"""Iteración 55 · Cuentas para compras, armado, atención y portería. Spec: docs/desarrollo/55-personal-por-rol.md."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_settlement import CYCLE, NOW, Scenario
from web_client import fast_hashing

from yapa_sdd import customers, notices, partners, reception, wallet
from yapa_sdd.auth import authenticate, set_admin_password, set_pin
from yapa_sdd.buffer import add_to_buffer
from yapa_sdd.claims import file_claim, review_claim
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import deliver_zone, pack_bag
from yapa_sdd.settlement import settle_cycle
from yapa_sdd.web.api import create_api


ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"
PASS = "personal-2026"
BUYER, PACKER, SUPPORT, CONCIERGE = "compras-1", "armado-1", "atencion-1", "porteria-jm"
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
SUNDAY = datetime(2026, 9, 20, 8, 0, tzinfo=LIMA)
IN_BUILDING = "Tus bolsas ya están en el edificio"


class Base(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)
        self.first = self.orders[0]

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def staff(self, user, kind, name="Persona del equipo", zone_id=None, by=ADMIN, password=PASS):
        return partners.create_staff(self.store, user, kind, name, password, by=by, now=NOW, zone_id=zone_id)

    def packer(self):
        return self.staff(PACKER, partners.PACKER, "Rosa Armado")

    def concierge(self, user=CONCIERGE, zone_id="Z-JM-01"):
        return self.staff(user, partners.CONCIERGE, "Sr. Ramos", zone_id=zone_id)

    def pack_all(self, by=ADMIN):
        for order in self.orders:
            pack_bag(self.store, order.order_id, by=by, photo="fotos/bolsa.jpg", now=FRIDAY)

    def deliver(self):
        self.pack_all()
        return deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/entrega.jpg", received_by="Sr. Ramos",
                            now=SATURDAY)

    def confirm(self, by=CONCIERGE, zone_id="Z-JM-01", now=SATURDAY):
        return reception.confirm_reception(self.store, CYCLE, zone_id, by=by, now=now)


class AccountTests(Base):
    # CX-J (motor)
    def test_cx_j_admin_creates_the_four_staff_accounts(self):
        for user, kind in ((BUYER, "compras"), (PACKER, "armador"), (SUPPORT, "atencion")):
            account = self.staff(user, kind)
            self.assertEqual((account.kind, account.active), (kind, True))
            self.assertEqual(authenticate(self.store, kind, user, PASS, NOW), user)
        account = self.concierge()
        self.assertEqual((account.kind, account.zone_id), ("porteria", "Z-JM-01"))

    # CX-K
    def test_cx_k_only_admin_creates_staff_accounts(self):
        self.packer()
        self.assertRule("NOT_AUTHORIZED", self.staff, "otro-1", partners.BUYER, by=PACKER)

    # CX-L
    def test_cx_l_concierge_needs_existing_zone(self):
        self.assertRule("ZONE_NOT_FOUND", self.concierge, zone_id="Z-NO-EXISTE")
        self.assertRule("ZONE_NOT_FOUND", self.concierge, zone_id=None)

    # CX-M
    def test_cx_m_name_and_unique_user(self):
        self.assertRule("NAME_REQUIRED", self.staff, PACKER, partners.PACKER, name="  ")
        self.packer()
        self.assertRule("USER_TAKEN", self.staff, PACKER, partners.SUPPORT)
        self.assertRule("INVALID_PASSWORD", self.staff, "otro-1", partners.SUPPORT, password="123456789")

    def test_cx_unknown_staff_kind_is_rejected(self):
        self.assertRule("INVALID_INPUT", self.staff, "otro-1", "gerente")


class PackerTests(Base):
    # AM-A (motor)
    def test_am_a_packer_packs_a_bag(self):
        self.packer()
        bag = pack_bag(self.store, self.first.order_id, by=PACKER, photo="fotos/bolsa.jpg", now=FRIDAY)
        self.assertEqual((bag.number, bag.packed_by), (1, PACKER))

    # AM-B
    def test_am_b_deactivated_packer_and_driver_cannot_pack(self):
        self.packer()
        partners.deactivate(self.store, PACKER, by=ADMIN)
        self.assertRule("NOT_AUTHORIZED", pack_bag, self.store, self.first.order_id, by=PACKER, photo="fotos/b.jpg",
                        now=FRIDAY)
        partners.create_driver(self.store, "reparto-1", "Pedro", PASS, by=ADMIN, now=NOW)
        self.assertRule("NOT_AUTHORIZED", pack_bag, self.store, self.first.order_id, by="reparto-1",
                        photo="fotos/b.jpg", now=FRIDAY)


class BuyerTests(Base):
    # CP-B
    def test_cp_b_buyer_adds_to_buffer(self):
        self.staff(BUYER, partners.BUYER)
        stock = add_to_buffer(self.store, CYCLE, "LIMPIATODO-GALON", "2", by=BUYER)
        self.assertEqual(stock.quantity, D("2"))

    # CP-C
    def test_cp_c_buyer_follows_buffer_rules(self):
        self.staff(BUYER, partners.BUYER)
        self.assertRule("PERISHABLE_NOT_ALLOWED", add_to_buffer, self.store, CYCLE, "PAPA-AMARILLA", "5", by=BUYER)

    # CP-D
    def test_cp_d_packer_does_not_touch_buffer(self):
        self.packer()
        self.assertRule("NOT_AUTHORIZED", add_to_buffer, self.store, CYCLE, "LIMPIATODO-GALON", "2", by=PACKER)


class SupportTests(Base):
    def claim(self):
        self.deliver()
        claim = file_claim(self.store, self.first.order_id, customer_id=self.first.customer_id, product_id="CEBOLLA-ROJA",
                           quantity="1", reason="FALTANTE", photo="fotos/cebolla.jpg", now=SUNDAY)
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        return claim

    # AT-A
    def test_at_a_support_approves_claim(self):
        self.staff(SUPPORT, partners.SUPPORT)
        claim = self.claim()
        before = wallet.balance(self.store, self.first.customer_id)
        reviewed = review_claim(self.store, claim.claim_id, by=SUPPORT, approve=True, now=SUNDAY)
        self.assertEqual(reviewed.status, "APROBADO")
        self.assertGreater(wallet.balance(self.store, self.first.customer_id), before)

    # AT-B
    def test_at_b_packer_does_not_review_claims(self):
        self.packer()
        claim = self.claim()
        self.assertRule("NOT_AUTHORIZED", review_claim, self.store, claim.claim_id, by=PACKER, approve=False, now=SUNDAY)

    # AT-C
    def test_at_c_support_handles_pin_requests(self):
        self.staff(SUPPORT, partners.SUPPORT)
        customers.request_pin_help(self.store, "101", NOW)
        customers.request_pin_help(self.store, "105", NOW)
        first, second = sorted(self.store.pin_requests)
        customers.dismiss_pin_request(self.store, first, by=SUPPORT)
        pin = customers.reset_pin(self.store, 105, by=SUPPORT)
        self.assertEqual((len(pin), self.store.pin_requests), (6, {}))
        self.packer()
        self.assertRule("NOT_AUTHORIZED", customers.reset_pin, self.store, 101, by=PACKER)


class ReceptionTests(Base):
    # PO-A (motor)
    def test_po_a_concierge_sees_its_zone_without_money(self):
        self.concierge()
        self.deliver()
        view = reception.for_zone(self.store, CYCLE, "Z-JM-01")
        self.assertEqual(view["estado"], "entregada")
        self.assertEqual(len(view["pedidos"]), 8)
        self.assertEqual(view["pedidos"][0], {"id": self.first.order_id, "vecino": f"Vecino {self.first.customer_id}",
                                              "bolsas": 1})

    # PO-B
    def test_po_b_concierge_confirms_and_neighbors_are_told(self):
        self.concierge()
        self.deliver()
        confirmed = self.confirm()
        self.assertEqual((confirmed.received_by, confirmed.zone_id), (CONCIERGE, "Z-JM-01"))
        self.assertEqual(reception.for_zone(self.store, CYCLE, "Z-JM-01")["estado"], "recibida")
        notices.in_building(self.store, confirmed, SATURDAY)  # la API lo manda con tell (AV-11)
        for order in self.orders:
            titles = [n.title for n in notices.for_customer(self.store, order.customer_id)]
            self.assertIn(IN_BUILDING, titles)

    # PO-C
    def test_po_c_confirms_only_once(self):
        self.concierge()
        self.deliver()
        self.confirm()
        self.assertRule("ALREADY_CONFIRMED", self.confirm)

    # PO-D
    def test_po_d_needs_a_registered_delivery(self):
        self.concierge()
        self.assertRule("DELIVERY_NOT_FOUND", self.confirm)

    # PO-E
    def test_po_e_concierge_of_other_zone(self):
        self.concierge("porteria-lince", "Z-LINCE-01")
        self.deliver()
        self.assertRule("FOREIGN_ZONE", self.confirm, by="porteria-lince")

    # PO-F (motor)
    def test_po_f_zone_admin_confirms_other_neighbor_cannot(self):
        self.store.zones["Z-JM-01"].admin_id = self.first.customer_id
        self.deliver()
        self.assertRule("FOREIGN_ZONE", self.confirm, by=self.orders[1].customer_id)
        self.assertEqual(self.confirm(by=self.first.customer_id).received_by, str(self.first.customer_id))

    # PO-G
    def test_po_g_other_accounts_cannot_confirm(self):
        self.packer()
        self.deliver()
        self.assertRule("NOT_AUTHORIZED", self.confirm, by=PACKER)
        self.assertRule("NOT_AUTHORIZED", self.confirm, by=ADMIN)

    def test_po_deactivated_concierge_cannot_confirm(self):
        self.concierge()
        self.deliver()
        partners.deactivate(self.store, CONCIERGE, by=ADMIN)
        self.assertRule("NOT_AUTHORIZED", self.confirm)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        set_pin(self.store, 101, PIN)
        self.now = FRIDAY
        # sesiones con su propio reloj (DM-05), como en la iteración 54
        self.api = create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY)
        self.admin = ApiClient(self.api)
        self.assertEqual(self.admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)

    def client(self, user, kind, **extra):
        status, _, _ = self.admin.post("/api/admin/cuentas", {"tipo": kind, "usuario": user, "nombre": "Persona",
                                                              "contrasena": PASS, **extra})
        self.assertEqual(status, 201)
        client = ApiClient(self.api)
        status, data, _ = client.login(user, PASS, kind)
        self.assertEqual((status, data["rol"]), (200, kind))
        return client, data

    # CX-J (API)
    def test_cx_j_api_creates_staff_accounts(self):
        self.client(BUYER, "compras")
        self.client(PACKER, "armador")
        self.client(SUPPORT, "atencion")
        _, me = self.client(CONCIERGE, "porteria", zona="Z-JM-01")
        self.assertEqual(me["zona"], "Z-JM-01")
        status, data, _ = self.admin.get("/api/admin/cuentas")
        self.assertEqual({c["usuario"]: c["tipo"] for c in data["cuentas"]},
                         {BUYER: "compras", PACKER: "armador", SUPPORT: "atencion", CONCIERGE: "porteria"})
        self.assertEqual(next(c for c in data["cuentas"] if c["usuario"] == CONCIERGE)["zona"], "Z-JM-01")

    # CX-K (API)
    def test_cx_k_packer_cannot_create_accounts(self):
        packer, _ = self.client(PACKER, "armador")
        body = {"tipo": "compras", "usuario": "otro-1", "nombre": "X", "contrasena": PASS}
        self.assertEqual(packer.post("/api/admin/cuentas", body)[0], 403)

    # CX-N
    def test_cx_n_each_role_only_uses_its_routes(self):
        packer, _ = self.client(PACKER, "armador")
        support, _ = self.client(SUPPORT, "atencion")
        buyer, _ = self.client(BUYER, "compras")
        concierge, _ = self.client(CONCIERGE, "porteria", zona="Z-JM-01")
        driver, _ = self.client("reparto-1", "transportista")
        forbidden = [
            (packer, "/api/admin/reclamos"), (packer, "/api/compras"), (packer, "/api/admin/devoluciones"),
            (support, "/api/admin/catalogo"), (support, "/api/admin/armado"), (support, "/api/compras"),
            (buyer, "/api/admin/devoluciones"), (buyer, "/api/admin/conciliacion"), (buyer, "/api/admin/armado"),
            (concierge, "/api/admin/armado"), (concierge, "/api/reparto"), (concierge, "/api/mis-pedidos"),
            (driver, "/api/porteria"), (self.admin, "/api/porteria"),
        ]
        for client, path in forbidden:
            self.assertEqual(client.get(path)[0], 403, path)
        self.assertEqual(packer.post(f"/api/admin/pedidos/{self.first.order_id}/verificar")[0], 403)
        allowed = [(packer, "/api/admin/armado"), (support, "/api/admin/reclamos"), (support, "/api/admin/devoluciones"),
                   (support, "/api/admin/pin-solicitudes"), (buyer, "/api/compras"), (concierge, "/api/porteria"),
                   (self.admin, "/api/admin/armado"), (self.admin, "/api/compras")]
        for client, path in allowed:
            self.assertEqual(client.get(path)[0], 200, path)

    # AM-A (API)
    def test_am_a_packer_list_has_no_money(self):
        packer, _ = self.client(PACKER, "armador")
        status, data, _ = packer.get(f"/api/admin/armado?ciclo={CYCLE}")
        self.assertEqual((status, len(data["pedidos"])), (200, 8))
        for key in ("total", "pago", "codigo_pago", "a_yapear", "con_saldo"):
            self.assertNotIn(key, data["pedidos"][0])
        self.assertIn("lineas", data["pedidos"][0])
        status, bag, _ = packer.post("/api/admin/bolsas", {"pedido": self.first.order_id, "foto": "fotos/bolsa.jpg"})
        self.assertEqual((status, bag["numero"]), (200, 1))
        self.assertEqual(self.store.bags[self.first.order_id][0].packed_by, PACKER)
        status, data, _ = self.admin.get(f"/api/admin/armado?ciclo={CYCLE}")
        self.assertIn("total", data["pedidos"][0])

    # CP-A
    def test_cp_a_buyer_sees_purchase_by_supplier(self):
        settle_cycle(self.store, CYCLE, at=SATURDAY)
        self.now = SATURDAY
        buyer, _ = self.client(BUYER, "compras")
        status, data, _ = buyer.get(f"/api/compras?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        fresh = next(p for p in data["proveedores"] if p["id"] == "SUP-FRESCOS")
        self.assertFalse(fresh["parcial"])
        self.assertFalse(data["parcial"])
        quantities = {line["producto"]: line["cantidad"] for line in fresh["lineas"]}
        self.assertEqual(quantities, {"PAPA-AMARILLA": "40", "PAPA-BLANCA": "80", "CEBOLLA-ROJA": "80"})
        self.assertTrue(all({"desde", "precio", "monto"} <= set(line) for line in fresh["lineas"]))
        self.assertIn("total", fresh)
        self.assertEqual((data["colchon"]["valor"], data["colchon"]["tope"]), ("0.00", "500.00"))

    # CP-E
    def test_cp_e_open_cycle_is_partial_even_without_suppliers(self):
        buyer, _ = self.client(BUYER, "compras")
        status, data, _ = buyer.get("/api/compras?ciclo=2026-W40")
        self.assertEqual((status, data["proveedores"], data["parcial"]), (200, [], True))

    # CP-B (API)
    def test_cp_b_buyer_adds_and_uses_buffer_from_api(self):
        buyer, _ = self.client(BUYER, "compras")
        status, data, _ = buyer.post("/api/compras/colchon", {"ciclo": CYCLE, "producto": "LIMPIATODO-GALON",
                                                              "cantidad": "2"})
        self.assertEqual((status, data["cantidad"]), (200, "2"))
        status, data, _ = buyer.post("/api/compras/colchon", {"ciclo": CYCLE, "producto": "PAPA-AMARILLA",
                                                              "cantidad": "5"})
        self.assertEqual((status, data["error"]["codigo"]), (422, "PERISHABLE_NOT_ALLOWED"))
        status, data, _ = buyer.post("/api/compras/colchon/usar", {"producto": "LIMPIATODO-GALON", "cantidad": "1",
                                                                   "pedido": self.first.order_id})
        self.assertEqual((status, data["error"]["codigo"]), (422, "BUFFER_NOT_FOR_ORDER"))

    # AT-C (API)
    def test_at_c_support_resets_pin_from_api(self):
        support, _ = self.client(SUPPORT, "atencion")
        status, data, _ = support.post("/api/admin/vecinos/105/pin")
        self.assertEqual((status, len(data["pin"])), (200, 6))

    # PO-A, PO-B (API)
    def test_po_concierge_flow_from_api(self):
        concierge, _ = self.client(CONCIERGE, "porteria", zona="Z-JM-01")
        status, data, _ = concierge.get(f"/api/porteria?ciclo={CYCLE}")
        self.assertEqual((status, data["estado"]), (200, "pendiente"))
        status, data, _ = concierge.post("/api/porteria/recepciones", {"ciclo": CYCLE})
        self.assertEqual((status, data["error"]["codigo"]), (422, "DELIVERY_NOT_FOUND"))
        self.deliver()
        self.now = SATURDAY
        status, data, _ = concierge.get(f"/api/porteria?ciclo={CYCLE}")
        self.assertEqual((data["estado"], len(data["pedidos"])), ("entregada", 8))
        text = str(data)
        for word in ("total", "monto", "PAPA", "celular"):
            self.assertNotIn(word, text)
        status, data, _ = concierge.post("/api/porteria/recepciones", {"ciclo": CYCLE})
        self.assertEqual((status, data["estado"]), (200, "recibida"))
        titles = [n.title for n in notices.for_customer(self.store, self.first.customer_id)]
        self.assertIn(IN_BUILDING, titles)

    # PO-F (API)
    def test_po_f_zone_admin_confirms_from_api(self):
        self.store.zones["Z-JM-01"].admin_id = self.first.customer_id
        set_pin(self.store, self.first.customer_id, PIN)
        self.deliver()
        self.now = SATURDAY
        neighbor = ApiClient(self.api)
        self.assertEqual(neighbor.login(self.first.customer_id, PIN)[0], 200)
        status, data, _ = neighbor.get(f"/api/zona/recepcion?ciclo={CYCLE}")
        self.assertEqual((status, data["estado"]), (200, "entregada"))
        status, data, _ = neighbor.post("/api/zona/recepciones", {"ciclo": CYCLE})
        self.assertEqual((status, data["estado"]), (200, "recibida"))
        other = ApiClient(self.api)
        self.assertEqual(other.login(101, PIN)[0], 200)
        status, data, _ = other.get(f"/api/zona/recepcion?ciclo={CYCLE}")
        self.assertEqual((status, data["error"]["codigo"]), (422, "FOREIGN_ZONE"))


if __name__ == "__main__":
    unittest.main()
