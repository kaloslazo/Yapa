"""Iteración 54 · Cuentas para proveedores y transportistas. Spec: docs/desarrollo/54-proveedores-y-transportistas.md."""

from datetime import datetime
from decimal import Decimal as D
import unittest

from api_client import ApiClient
from test_settlement import CYCLE, NOW, Scenario
from web_client import fast_hashing

from yapa_sdd import partners, supplier_offers
from yapa_sdd.auth import authenticate, set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.fulfillment import deliver_zone, pack_bag, register_failed_delivery
from yapa_sdd.web.api import create_api


ADMIN, ADMIN_PASS, PIN = "admin-yapa", "yapa-admin-2026", "482915"
DRIVER, DRIVER_PASS = "reparto-1", "reparto-2026"
SUPPLIER, SUPPLIER_PASS = "frescos", "frescos-2026"
W39 = "2026-W39"
FRIDAY = datetime(2026, 9, 18, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
MONDAY = datetime(2026, 9, 21, 10, 0, tzinfo=LIMA)
OFFER = "codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1,desde2,precio2\n" \
        "PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,300,,0,3.40,100,3.20"


class Base(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.s = Scenario()
        self.store = self.s.store
        self.orders = self.s.orders("Z-JM-01", 8)

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def driver(self, user=DRIVER, password=DRIVER_PASS, by=ADMIN):
        return partners.create_driver(self.store, user, "Pedro Reparto", password, by=by, now=NOW)

    def supplier(self, user=SUPPLIER, supplier_id="SUP-FRESCOS", name="", by=ADMIN):
        return partners.create_supplier_account(self.store, user, supplier_id, SUPPLIER_PASS, by=by, now=NOW, name=name)

    def pack_all(self):
        for order in self.orders:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)

    def offer(self, text=OFFER, now=SATURDAY, by=SUPPLIER):
        return supplier_offers.submit_offer(self.store, W39, text, by=by, now=now)


class AccountTests(Base):
    # CX-A (motor)
    def test_cx_a_admin_creates_driver_that_can_log_in(self):
        account = self.driver()
        self.assertEqual((account.kind, account.active), ("transportista", True))
        self.assertEqual(authenticate(self.store, "transportista", DRIVER, DRIVER_PASS, NOW), DRIVER)

    # CX-B
    def test_cx_b_invalid_user(self):
        self.assertRule("INVALID_USER", self.driver, user="Reparto 1")
        self.assertRule("INVALID_USER", self.driver, user="ab")

    # CX-C
    def test_cx_c_user_taken(self):
        self.assertRule("USER_TAKEN", self.driver, user=ADMIN)
        self.driver()
        self.assertRule("USER_TAKEN", self.driver)
        self.assertRule("USER_TAKEN", self.supplier, user=DRIVER)

    # CX-D
    def test_cx_d_short_password(self):
        self.assertRule("INVALID_PASSWORD", self.driver, password="123456789")

    # CX-E
    def test_cx_e_only_admin_creates(self):
        self.assertRule("NOT_AUTHORIZED", self.driver, by="101")
        self.driver()
        self.assertRule("NOT_AUTHORIZED", self.driver, user="reparto-2", by=DRIVER)

    def test_cx_d_driver_needs_name(self):
        self.assertRule("NAME_REQUIRED", partners.create_driver, self.store, DRIVER, "  ", DRIVER_PASS, by=ADMIN, now=NOW)

    # CX-F
    def test_cx_f_supplier_must_be_allied(self):
        self.assertRule("SUPPLIER_NOT_ALLIED", self.supplier, supplier_id="SUP-OTRO")
        self.assertRule("SUPPLIER_NOT_FOUND", self.supplier, supplier_id="SUP-NADIE")

    # CX-G
    def test_cx_g_new_supplier_is_registered_as_allied(self):
        account = self.supplier(supplier_id="SUP-NUEVO", name="Mercado Mayorista Norte")
        self.assertEqual(account.supplier_id, "SUP-NUEVO")
        self.assertTrue(self.store.suppliers["SUP-NUEVO"].allied)
        self.assertEqual(self.store.suppliers["SUP-NUEVO"].name, "Mercado Mayorista Norte")

    # CX-H (motor)
    def test_cx_h_deactivated_account_cannot_log_in_until_new_password(self):
        self.driver()
        partners.deactivate(self.store, DRIVER, by=ADMIN)
        self.assertRule("INVALID_CREDENTIALS", authenticate, self.store, "transportista", DRIVER, DRIVER_PASS, NOW)
        partners.set_password(self.store, DRIVER, "otra-clave-2026", by=ADMIN)
        self.assertTrue(self.store.partners[DRIVER].active)
        self.assertEqual(authenticate(self.store, "transportista", DRIVER, "otra-clave-2026", NOW), DRIVER)


class DriverTests(Base):
    def setUp(self):
        super().setUp()
        self.driver()

    def deliver(self, by=DRIVER):
        return deliver_zone(self.store, CYCLE, "Z-JM-01", by=by, photo="fotos/entrega.jpg", received_by="Sr. Ramos",
                            now=SATURDAY)

    # TR-B (motor)
    def test_tr_b_driver_delivers_a_zone(self):
        self.pack_all()
        self.assertEqual(self.deliver().delivered_by, DRIVER)

    # TR-C
    def test_tr_c_cannot_deliver_unpacked_orders(self):
        for order in self.orders[1:]:
            pack_bag(self.store, order.order_id, by=ADMIN, photo="fotos/bolsa.jpg", now=FRIDAY)
        self.assertRule("ORDERS_NOT_PACKED", self.deliver)

    # TR-D
    def test_tr_d_driver_registers_failed_delivery(self):
        self.pack_all()
        failure = register_failed_delivery(self.store, CYCLE, "Z-JM-01", by=DRIVER, photo="fotos/puerta.jpg",
                                           reason="PORTERIA_CERRADA", now=SATURDAY)
        self.assertEqual(failure.registered_by, DRIVER)

    # TR-E
    def test_tr_e_driver_does_not_pack(self):
        self.assertRule("NOT_AUTHORIZED", pack_bag, self.store, self.orders[0].order_id, by=DRIVER,
                        photo="fotos/bolsa.jpg", now=FRIDAY)

    # TR-F
    def test_tr_f_deactivated_driver_cannot_deliver(self):
        self.pack_all()
        partners.deactivate(self.store, DRIVER, by=ADMIN)
        self.assertRule("NOT_AUTHORIZED", self.deliver)

    def test_tr_f_supplier_cannot_deliver(self):
        self.pack_all()
        self.supplier()
        self.assertRule("NOT_AUTHORIZED", self.deliver, by=SUPPLIER)


class OfferTests(Base):
    def setUp(self):
        super().setUp()
        self.supplier()

    # PV-A
    def test_pv_a_offer_stays_pending_and_catalog_does_not_change(self):
        offer = self.offer()
        self.assertEqual((offer.status, offer.supplier_id), ("PENDIENTE", "SUP-FRESCOS"))
        self.assertEqual(offer.products[0].supplier_id, "SUP-FRESCOS")
        self.assertNotIn(W39, self.store.catalogs)

    # PV-B
    def test_pv_b_cycle_already_open(self):
        self.assertRule("CATALOG_LOCKED", self.offer, now=MONDAY)

    # PV-C
    def test_pv_c_foreign_supplier_column(self):
        self.assertRule("FOREIGN_SUPPLIER", self.offer, OFFER.replace(",300,,", ",300,SUP-LIMPIEZA,"))

    # PV-D
    def test_pv_d_foreign_product(self):
        line = "\nLIMPIATODO-GALON,Limpiatodo,LIMPIEZA,unidad,1,60,,0,7.50,12,6.50"
        self.assertRule("FOREIGN_PRODUCT", self.offer, OFFER + line)

    # PV-E
    def test_pv_e_invalid_tiers(self):
        self.assertRule("INVALID_TIERS", self.offer, OFFER.replace("100,3.20", "100,3.60"))
        self.assertRule("INVALID_CATALOG_FORMAT", self.offer, "nada que ver")

    def test_pv_only_supplier_accounts_send_offers(self):
        self.driver()
        self.assertRule("NOT_AUTHORIZED", self.offer, by=DRIVER)
        self.assertRule("NOT_AUTHORIZED", self.offer, by=ADMIN)

    # PV-F
    def test_pv_f_approval_replaces_only_that_supplier_products(self):
        self.offer()
        offer = supplier_offers.approve_offer(self.store, W39, "SUP-FRESCOS", by=ADMIN, now=SATURDAY)
        self.assertEqual(offer.status, "APROBADA")
        catalog = self.store.catalogs[W39]
        self.assertEqual([t.base_price for t in catalog["PAPA-AMARILLA"].tiers], [D("3.40"), D("3.20")])
        self.assertNotIn("CEBOLLA-ROJA", catalog)
        self.assertIn("LIMPIATODO-GALON", catalog)

    def test_pv_f_only_admin_approves(self):
        self.offer()
        self.assertRule("NOT_AUTHORIZED", supplier_offers.approve_offer, self.store, W39, "SUP-FRESCOS",
                        by=SUPPLIER, now=SATURDAY)
        self.assertRule("OFFER_NOT_FOUND", supplier_offers.approve_offer, self.store, W39, "SUP-LIMPIEZA",
                        by=ADMIN, now=SATURDAY)

    # PV-G
    def test_pv_g_cannot_approve_twice(self):
        self.offer()
        supplier_offers.approve_offer(self.store, W39, "SUP-FRESCOS", by=ADMIN, now=SATURDAY)
        self.assertRule("OFFER_NOT_PENDING", supplier_offers.approve_offer, self.store, W39, "SUP-FRESCOS",
                        by=ADMIN, now=SATURDAY)

    # PV-H
    def test_pv_h_reject_needs_reason(self):
        self.offer()
        self.assertRule("REASON_REQUIRED", supplier_offers.reject_offer, self.store, W39, "SUP-FRESCOS", "  ",
                        by=ADMIN, now=SATURDAY)
        offer = supplier_offers.reject_offer(self.store, W39, "SUP-FRESCOS", "Falta la cebolla", by=ADMIN, now=SATURDAY)
        self.assertEqual((offer.status, offer.reason), ("RECHAZADA", "Falta la cebolla"))

    # PV-I
    def test_pv_i_resend_after_rejection_is_pending_again(self):
        self.offer()
        supplier_offers.reject_offer(self.store, W39, "SUP-FRESCOS", "Falta la cebolla", by=ADMIN, now=SATURDAY)
        self.assertEqual(self.offer().status, "PENDIENTE")

    # PV-J
    def test_pv_j_consolidated_order_after_close(self):
        result = supplier_offers.supplier_order(self.store, CYCLE, "SUP-FRESCOS", FRIDAY)
        self.assertFalse(result["parcial"])
        quantities = {line["producto"]: line["cantidad"] for line in result["lineas"]}
        self.assertEqual(quantities, {"PAPA-AMARILLA": D("40"), "PAPA-BLANCA": D("80"), "CEBOLLA-ROJA": D("80")})
        papa = next(line for line in result["lineas"] if line["producto"] == "PAPA-AMARILLA")
        product = self.store.catalog_for(CYCLE)["PAPA-AMARILLA"]
        tier = product.tier_for(D("40"))
        self.assertEqual((papa["desde"], papa["precio"], papa["monto"]),
                         (tier.min_quantity, tier.base_price, D("40") * tier.base_price))
        self.assertEqual(result["total"], sum(line["monto"] for line in result["lineas"]))
        self.assertEqual(supplier_offers.supplier_order(self.store, CYCLE, "SUP-LIMPIEZA", FRIDAY)["lineas"], [])

    # PV-K
    def test_pv_k_partial_before_close(self):
        self.assertTrue(supplier_offers.supplier_order(self.store, CYCLE, "SUP-FRESCOS", NOW)["parcial"])


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        set_pin(self.store, 101, PIN)
        self.now = FRIDAY
        # sesiones con su propio reloj (DM-05): el negocio salta al sábado sin que venzan
        self.api = create_api(self.store, clock=lambda: self.now, security_clock=lambda: FRIDAY)
        self.admin = ApiClient(self.api)
        self.assertEqual(self.admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)

    def create(self, body):
        return self.admin.post("/api/admin/cuentas", body)

    def driver_client(self):
        status, _, _ = self.create({"tipo": "transportista", "usuario": DRIVER, "nombre": "Pedro", "contrasena": DRIVER_PASS})
        self.assertEqual(status, 201)
        client = ApiClient(self.api)
        status, data, _ = client.login(DRIVER, DRIVER_PASS, "transportista")
        self.assertEqual((status, data["rol"]), (200, "transportista"))
        return client

    def supplier_client(self):
        status, _, _ = self.create({"tipo": "proveedor", "usuario": SUPPLIER, "proveedor": "SUP-FRESCOS",
                                    "contrasena": SUPPLIER_PASS})
        self.assertEqual(status, 201)
        client = ApiClient(self.api)
        status, data, _ = client.login(SUPPLIER, SUPPLIER_PASS, "proveedor")
        self.assertEqual((status, data["rol"]), (200, "proveedor"))
        return client

    # CX-A (API)
    def test_cx_a_api_creates_and_lists_accounts(self):
        self.driver_client()
        self.supplier_client()
        status, data, _ = self.admin.get("/api/admin/cuentas")
        self.assertEqual(status, 200)
        self.assertEqual({c["usuario"]: c["tipo"] for c in data["cuentas"]}, {DRIVER: "transportista", SUPPLIER: "proveedor"})

    # CX-E (API)
    def test_cx_e_neighbor_and_driver_cannot_create_accounts(self):
        driver = self.driver_client()
        vecino = ApiClient(self.api)
        vecino.login(101, PIN)
        body = {"tipo": "transportista", "usuario": "otro", "nombre": "X", "contrasena": DRIVER_PASS}
        self.assertEqual(vecino.post("/api/admin/cuentas", body)[0], 403)
        self.assertEqual(driver.post("/api/admin/cuentas", body)[0], 403)

    # CX-H (API)
    def test_cx_h_deactivation_closes_session(self):
        driver = self.driver_client()
        self.assertEqual(self.admin.post(f"/api/admin/cuentas/{DRIVER}/desactivar")[0], 200)
        self.assertEqual(driver.get("/api/reparto")[0], 401)
        status, data, _ = ApiClient(self.api).login(DRIVER, DRIVER_PASS, "transportista")
        self.assertEqual((status, data["error"]["codigo"]), (422, "INVALID_CREDENTIALS"))
        self.assertEqual(self.admin.post(f"/api/admin/cuentas/{DRIVER}/contrasena", {"contrasena": "nueva-clave-26"})[0], 200)
        self.assertEqual(ApiClient(self.api).login(DRIVER, "nueva-clave-26", "transportista")[0], 200)

    # CX-I
    def test_cx_i_each_account_only_uses_its_routes(self):
        driver = self.driver_client()
        supplier = self.supplier_client()
        self.assertEqual(driver.get("/api/admin/armado")[0], 403)
        self.assertEqual(driver.get("/api/mis-pedidos")[0], 403)
        self.assertEqual(driver.get("/api/proveedor")[0], 403)
        self.assertEqual(supplier.get("/api/reparto")[0], 403)
        self.assertEqual(supplier.get("/api/admin/catalogo")[0], 403)
        self.assertEqual(self.admin.get("/api/reparto")[0], 403)

    # TR-A
    def test_tr_a_route_without_neighbor_data(self):
        self.pack_all()
        driver = self.driver_client()
        status, data, _ = driver.get(f"/api/reparto?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["paradas"]), 1)
        stop = data["paradas"][0]
        self.assertEqual((stop["zona"]["id"], stop["estado"]), ("Z-JM-01", "pendiente"))
        self.assertEqual(len(stop["pedidos"]), 8)
        self.assertTrue(all(p["bolsas"] == 1 for p in stop["pedidos"]))
        text = str(data)
        for customer in self.store.customers.values():
            self.assertNotIn(customer.name, text)
        self.assertNotIn("total", str(stop["pedidos"]))

    # TR-B (API)
    def test_tr_b_driver_delivers_from_api(self):
        self.pack_all()
        self.now = SATURDAY
        driver = self.driver_client()
        status, _, _ = driver.post("/api/reparto/entregas", {"ciclo": CYCLE, "zona": "Z-JM-01", "foto": "fotos/e.jpg",
                                                              "recibe": "Sr. Ramos"})
        self.assertEqual(status, 200)
        self.assertEqual(self.store.deliveries[(CYCLE, "Z-JM-01")].delivered_by, DRIVER)
        self.assertEqual(driver.get(f"/api/reparto?ciclo={CYCLE}")[1]["paradas"][0]["estado"], "entregada")

    # TR-D (API)
    def test_tr_d_failed_delivery_from_api(self):
        self.pack_all()
        self.now = SATURDAY
        driver = self.driver_client()
        status, _, _ = driver.post("/api/reparto/entregas-fallidas", {"ciclo": CYCLE, "zona": "Z-JM-01",
                                                                       "foto": "fotos/p.jpg", "motivo": "PORTERIA_CERRADA"})
        self.assertEqual(status, 200)
        self.assertEqual(driver.get(f"/api/reparto?ciclo={CYCLE}")[1]["paradas"][0]["estado"], "fallida")

    # PV-A, PV-F, PV-H (API)
    def test_pv_offer_flow_from_api(self):
        self.now = SATURDAY
        supplier = self.supplier_client()
        status, data, _ = supplier.post("/api/proveedor/propuestas", {"ciclo": W39, "lista": OFFER})
        self.assertEqual((status, data["estado"]), (201, "PENDIENTE"))
        status, data, _ = self.admin.get("/api/admin/propuestas")
        self.assertEqual([(p["ciclo"], p["proveedor"], p["estado"]) for p in data["propuestas"]],
                         [(W39, "SUP-FRESCOS", "PENDIENTE")])
        status, data, _ = self.admin.post(f"/api/admin/propuestas/{W39}/SUP-FRESCOS/rechazar", {"motivo": "Falta la cebolla"})
        self.assertEqual((status, data["estado"]), (200, "RECHAZADA"))
        status, data, _ = supplier.get("/api/proveedor")
        self.assertEqual(data["propuestas"][0]["motivo"], "Falta la cebolla")
        supplier.post("/api/proveedor/propuestas", {"ciclo": W39, "lista": OFFER})
        status, data, _ = self.admin.post(f"/api/admin/propuestas/{W39}/SUP-FRESCOS/aprobar")
        self.assertEqual((status, data["estado"]), (200, "APROBADA"))
        self.assertIn("PAPA-AMARILLA", self.store.catalogs[W39])

    # PV-J (API)
    def test_pv_j_supplier_sees_its_order(self):
        supplier = self.supplier_client()
        status, data, _ = supplier.get(f"/api/proveedor?ciclo={CYCLE}")
        self.assertEqual(status, 200)
        self.assertFalse(data["pedido"]["parcial"])
        self.assertEqual({l["producto"]: l["cantidad"] for l in data["pedido"]["lineas"]},
                         {"PAPA-AMARILLA": "40", "PAPA-BLANCA": "80", "CEBOLLA-ROJA": "80"})
        for customer in self.store.customers.values():
            self.assertNotIn(customer.name, str(data))


if __name__ == "__main__":
    unittest.main()
