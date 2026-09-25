"""AU-C: una semana completa por la web, con la conciliación en 0 después de cada paso."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from web_client import WebClient, fast_hashing

from yapa_sdd.audit import money_balance
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer
from yapa_sdd.seed import pilot_store
from yapa_sdd.wallet import balance
from yapa_sdd.web.app import create_app


WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
SATURDAY_NOON = datetime(2026, 9, 19, 12, 0, tzinfo=LIMA)
CYCLE = "2026-W38"
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
BASKET = {"cant_PAPA-AMARILLA": "5", "cant_PAPA-BLANCA": "10", "cant_CEBOLLA-ROJA": "10"}  # S/ 61.00
JM = list(range(801, 810))  # 9 vecinos de Jesús María
LINCE = [811, 812]  # 2 vecinos de Lince: su grupo no llega al mínimo


class WholeWeekTest(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        for customer_id in JM:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", "Z-JM-01"))
        for customer_id in LINCE:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", "Z-LINCE-01"))
        for customer_id in JM + LINCE:
            set_pin(self.store, customer_id, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.now = WEDNESDAY
        self.app = create_app(self.store, clock=lambda: self.now)

    def at(self, moment):
        self.now = moment

    def neighbor(self, customer_id):
        client = WebClient(self.app)
        client.login(customer_id, PIN)
        return client

    def admin(self):
        client = WebClient(self.app)
        client.login(ADMIN, ADMIN_PASS, kind="admin")
        return client

    def assertBalanced(self, step):
        with self.subTest(paso=step):
            self.assertEqual(money_balance(self.store).difference, D("0"))

    def test_au_c_whole_week(self):
        # 1. Miércoles: pedidos, verificación y una cancelación a saldo
        admin = self.admin()
        for customer_id in JM + LINCE:
            status, _, _ = self.neighbor(customer_id).post(
                "/pedidos", dict(BASKET, metodo="YAPE", codigo=f"OP-{customer_id}", monto="61.00", saldo="0"))
            self.assertEqual(status, 200)
        self.assertBalanced("pedidos registrados")
        for order_id in self.store.orders:
            self.assertEqual(admin.post("/admin/verificar", {"pedido": str(order_id)})[0], 200)
        self.assertBalanced("pagos verificados")
        status, _, _ = self.neighbor(809).post("/cuenta/cancelar", {"pedido": "9", "destino": "SALDO"})
        self.assertEqual(status, 200)
        self.assertEqual(balance(self.store, 809), D("61.00"))
        self.assertBalanced("cancelación a saldo")

        # 2. Sábado: armado y entrega de Jesús María
        self.at(SATURDAY)
        admin = self.admin()
        for order_id in range(1, 9):
            self.assertEqual(admin.post("/admin/bolsa", {"pedido": str(order_id), "foto": f"b{order_id}.jpg"})[0], 200)
        status, _, _ = admin.post("/admin/entrega", {"ciclo": CYCLE, "zona": "Z-JM-01", "foto": "entrega.jpg",
                                                     "recibe": "Sr. Ramos"})
        self.assertEqual(status, 200)
        self.assertBalanced("entrega")

        # 3. Liquidación
        status, _, html = admin.post("/admin/liquidar", {"ciclo": CYCLE})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.orders[1].status, "LIQUIDADO")
        self.assertEqual(self.store.orders[10].status, "NO_ATENDIDO")
        self.assertBalanced("liquidación")

        # 4. Reclamo aprobado
        self.at(SATURDAY_NOON)
        vecino = self.neighbor(801)
        status, _, _ = vecino.post("/reclamos", {"articulo": "1:CEBOLLA-ROJA", "cantidad": "1", "motivo": "FALTANTE",
                                                 "foto": "faltante.jpg"})
        self.assertEqual(status, 200)
        admin = self.admin()
        claim_id = next(iter(self.store.claims))
        self.assertEqual(admin.post("/admin/reclamos/revisar", {"reclamo": str(claim_id), "decision": "aprobar"})[0],
                         200)
        self.assertBalanced("reclamo aprobado")

        # 5. Devolución del saldo pedida y pagada
        self.assertEqual(balance(self.store, 801), D("5.38"))  # 3.36 de ahorro + 2.02 del reclamo
        self.assertEqual(vecino.post("/cuenta/devolucion", {"monto": "5.00"})[0], 200)
        refund_id = max(r.refund_id for r in self.store.refunds.values() if r.customer_id == 801)
        self.assertEqual(admin.post("/admin/devoluciones/pagar", {"reembolso": str(refund_id),
                                                                  "codigo": "YP-1"})[0], 200)
        self.assertBalanced("devolución pagada")

        # 6. Métricas y conciliación
        self.assertEqual(admin.get(f"/admin/metricas?ciclo={CYCLE}")[0], 200)
        status, _, html = admin.get("/admin/conciliacion")
        self.assertEqual(status, 200)
        self.assertIn("Cuadra", html)
        self.assertIn("S/ 0.00", html)
        final = money_balance(self.store)
        self.assertEqual(final.received, D("671.00"))  # 11 pedidos × S/ 61.00
        self.assertEqual(final.refunds_paid, D("5.00"))


if __name__ == "__main__":
    unittest.main()
