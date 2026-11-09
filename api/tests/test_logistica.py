"""Iteración 58 · Logística propia: cobro por Plin, flete, salida a reparto y seguimiento.

Spec: docs/desarrollo/58-logistica-propia.md.
"""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_settlement import CYCLE, Scenario, buy_all
from web_client import fast_hashing

from yapa_sdd import logistics, metrics, notices, partners
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import close_cycle, deliver_zone, pack_bag
from yapa_sdd.web import produccion
from yapa_sdd.web.api import create_api


ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"
PASS = "personal-2026"
BUYER, PACKER, DRIVER = "compras-1", "armado-1", "reparto-1"
BEFORE_CLOSE = datetime(2026, 9, 16, 19, 59, tzinfo=LIMA)
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 9, 0, tzinfo=LIMA)
PAYEE = {"numero": "999 000 111", "titular": "Yapa (cuenta de prueba)"}
STEPS = ["Pedido", "Pago verificado", "Comprado", "Armado", "En camino", "Entregado", "Te devolvemos"]


class Base(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)
        partners.create_staff(self.store, BUYER, partners.BUYER, "Compras", PASS, by=ADMIN, now=FRIDAY)
        partners.create_staff(self.store, PACKER, partners.PACKER, "Armado", PASS, by=ADMIN, now=FRIDAY)
        partners.create_driver(self.store, DRIVER, "Reparto", PASS, by=ADMIN, now=FRIDAY)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def freight(self, company="Fletes Santa Anita", amount="120.00", by=BUYER, now=FRIDAY):
        return logistics.register_freight(self.store, CYCLE, company, amount, by=by, now=now)

    def pack_all(self):
        for order in self.orders:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)

    def dispatch(self, zone_id="Z-JM-01", by=DRIVER):
        return logistics.dispatch_zone(self.store, CYCLE, zone_id, by=by, now=SATURDAY)

    def deliver(self):
        return deliver_zone(self.store, CYCLE, "Z-JM-01", by=ADMIN, photo="fotos/e.jpg", received_by="Sr. Ramos",
                            now=SATURDAY)

    def done(self, order_id=1):
        return [step["paso"] for step in logistics.tracking(self.store, self.store.orders[order_id]) if step["hecho"]]


class FreightSpecTests(Base):
    # FL-A
    def test_fl_a_register_once(self):
        freight = self.freight()
        self.assertEqual((freight.company, freight.amount), ("Fletes Santa Anita", D("120.00")))
        self.assertRule("FREIGHT_ALREADY_REGISTERED", self.freight)

    # FL-B
    def test_fl_b_invalid_data(self):
        for company in ("", "  ", "x" * 81):
            self.assertRule("INVALID_FREIGHT", self.freight, company=company)
        for amount in ("0", "-5", "2000.01", "abc", "10.005"):
            self.assertRule("INVALID_AMOUNT", self.freight, amount=amount)
        self.assertRule("CYCLE_STILL_OPEN", self.freight, now=BEFORE_CLOSE)
        self.assertRule("NOT_AUTHORIZED", self.freight, by=PACKER)
        self.assertRule("NOT_AUTHORIZED", self.freight, by=101)
        self.freight(by=ADMIN)


class RealMarginTests(Base):
    def settle(self):
        buy_all(self.store)
        self.pack_all()
        self.deliver()
        close_cycle(self.store, CYCLE, at=SATURDAY)

    # MR-A
    def test_mr_a_registered_freight_is_split_among_orders(self):
        self.freight()
        self.settle()
        costs, freight, estimated = logistics.real_costs(self.store, CYCLE)
        self.assertEqual((costs.purchase_trip, freight, estimated), (D("15.00"), D("120.00"), False))
        self.assertEqual((costs.packing, costs.support, costs.payment_fee_rate), (D("1.60"), D("0.73"), D("0")))
        contribution = metrics.order_margins(self.store, CYCLE)
        for order_id, net in metrics.net_margins(self.store, CYCLE, costs).items():
            self.assertEqual(net.net_margin, contribution[order_id].margin - D("15.00") - D("1.60") - D("0.73"))

    # MR-B
    def test_mr_b_estimated_when_not_registered(self):
        self.settle()
        costs, freight, estimated = logistics.real_costs(self.store, CYCLE)
        self.assertEqual((costs.purchase_trip, freight, estimated), (D("22.50"), D("180"), True))


class DispatchSpecTests(Base):
    # SR-A
    def test_sr_a_dispatch_tells_each_neighbor(self):
        buy_all(self.store)
        self.pack_all()
        self.dispatch()
        for order in self.orders:
            kinds = [n.kind for n in notices.for_customer(self.store, order.customer_id)]
            self.assertIn("EN_CAMINO", kinds)
        self.assertRule("ZONE_ALREADY_DISPATCHED", self.dispatch)
        self.assertEqual(len(self.deliver().order_ids), 8)

    # SR-B
    def test_sr_b_blocks(self):
        for order in self.orders[1:]:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)
        self.assertRule("ORDERS_NOT_PACKED", self.dispatch)
        pack_bag(self.store, 1, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)
        self.assertRule("PURCHASE_NOT_REGISTERED", self.dispatch)
        buy_all(self.store)
        self.assertRule("NOT_AUTHORIZED", self.dispatch, by=PACKER)
        self.assertRule("ZONE_NOT_FOUND", self.dispatch, zone_id="Z-NADA")
        self.deliver()
        self.assertRule("ZONE_ALREADY_CLOSED", self.dispatch)


class TrackingSpecTests(Base):
    # SG-A
    def test_sg_a_step_by_step(self):
        self.assertEqual([step["paso"] for step in logistics.tracking(self.store, self.store.orders[1])], STEPS)
        self.assertEqual(self.done(), STEPS[:2])
        buy_all(self.store)
        self.assertEqual(self.done(), STEPS[:3])
        self.pack_all()
        self.assertEqual(self.done(), STEPS[:4])
        self.dispatch()
        self.assertEqual(self.done(), STEPS[:5])
        self.deliver()
        self.assertEqual(self.done(), STEPS[:6])
        close_cycle(self.store, CYCLE, at=SATURDAY)
        self.assertEqual(self.done(), STEPS)

    # SG-B
    def test_sg_b_delivery_without_dispatch(self):
        buy_all(self.store)
        self.pack_all()
        self.deliver()
        self.assertEqual(self.done(), STEPS[:6])


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        set_pin(self.store, 101, PIN)
        self.now = FRIDAY

    def api(self, payee=None):
        return create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY, payee=payee)

    def login(self, api, user, secret, kind):
        client = ApiClient(api)
        self.assertEqual(client.login(user, secret, kind)[0], 200)
        return client

    # MR-C
    def test_mr_c_metrics_show_real_margin(self):
        api = self.api()
        buyer = self.login(api, BUYER, PASS, "compras")
        status, data, _ = buyer.post("/api/compras/flete", {"ciclo": CYCLE, "empresa": "Fletes Santa Anita", "monto": "120"})
        self.assertEqual((status, data["monto"]), (200, "120.00"))
        self.assertEqual(buyer.post("/api/compras/recibido", {"ciclo": CYCLE, "recibido": {}})[0], 200)
        self.pack_all()
        driver = self.login(api, DRIVER, PASS, "transportista")
        self.now = SATURDAY
        self.assertEqual(driver.post("/api/reparto/salidas", {"ciclo": CYCLE, "zona": "Z-JM-01"})[0], 200)
        status, data, _ = driver.get(f"/api/reparto?ciclo={CYCLE}")
        self.assertEqual(data["paradas"][0]["estado"], "en_camino")
        self.deliver()
        admin = self.login(api, ADMIN, ADMIN_PASS, "admin")
        self.assertEqual(admin.post(f"/api/admin/ciclos/{CYCLE}/liquidar")[0], 200)
        status, data, _ = admin.get(f"/api/admin/metricas?ciclo={CYCLE}")
        real = data["margen_real"]
        self.assertEqual((status, real["flete"], real["estimado"], real["por_pedido"]), (200, "120.00", False, "15.00"))
        self.assertIn("promedio", real)
        self.assertIn("pierden", real)

    # PL-A
    def test_pl_a_order_says_where_to_pay(self):
        self.now = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
        lines = {"PAPA-AMARILLA": "5", "PAPA-BLANCA": "10", "CEBOLLA-ROJA": "10"}
        for payee in (PAYEE, None):
            api = self.api(payee)
            store_orders = len(self.store.orders)
            neighbor = self.login(api, 101, PIN, "vecino")
            status, order, _ = neighbor.post("/api/pedidos", {"lineas": lines, "metodo": "PLIN"})
            self.assertEqual(status, 201, order)
            self.assertEqual(order.get("pagar_a"), payee)
            self.assertEqual(len(neighbor.get("/api/mis-pedidos")[1]["pedidos"][0]["seguimiento"]), 7)
            neighbor.post(f"/api/pedidos/{order['id']}/cancelar", {"destino": "SALDO"})
            self.assertEqual(len(self.store.orders), store_orders + 1)


class PayeeConfigTests(unittest.TestCase):
    # PL-A (configuración)
    def test_pl_a_payee_from_environment(self):
        env = {"YAPA_PLIN_NUMERO": "987 654 321", "YAPA_PLIN_TITULAR": "Yapa SAC"}
        self.assertEqual(produccion.payee(env, demo=False), {"numero": "987 654 321", "titular": "Yapa SAC"})
        self.assertIsNone(produccion.payee({}, demo=False))  # el servidor no inventa un número
        self.assertEqual(produccion.payee({}, demo=True), PAYEE)


if __name__ == "__main__":
    unittest.main()
