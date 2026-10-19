"""Iteración 42: avisos dentro de la app y por correo (docs/desarrollo/42-avisos.md)."""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal as D
import os
import tempfile
import unittest
from unittest import mock

from api_client import ApiClient
from test_cuenta_correo import FakeMailer
from web_client import fast_hashing

from yapa_sdd import notices, persistence
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import Customer, Zone
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

WEDNESDAY = datetime(2026, 9, 16, 10, 0, tzinfo=LIMA)
SATURDAY = datetime(2026, 9, 19, 10, 0, tzinfo=LIMA)
BASKET = {"PAPA-AMARILLA": "5", "PAPA-BLANCA": "10", "CEBOLLA-ROJA": "10"}  # S/ 61.00
PIN, ADMIN, ADMIN_PASS = "482915", "admin-yapa", "yapa-admin-2026"
ALAMOS, ARENALES, SAN_FELIPE = "Z-LINCE-01", "Z-LINCE-03", "Z-JM-01"
WEEK = list(range(801, 809))
EMAIL = "vecino801@gmail.com"


class AvisosBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        self.store.zones[ARENALES] = Zone(ARENALES, "Edificio Arenales", "Lince", "G-LINCE-3", D("40"),
                                          lat=-12.0852, lon=-77.0375)
        set_pin(self.store, 101, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.clock = [WEDNESDAY]
        self.mailer = FakeMailer()
        self.api = create_api(self.store, clock=lambda: self.clock[0], mailer=self.mailer, background_mail=False)
        for customer_id in WEEK:
            self.store.add_customer(Customer(customer_id, f"Vecino {customer_id}", SAN_FELIPE))
            set_pin(self.store, customer_id, PIN)

    def client(self, user=101):
        client = ApiClient(self.api)
        client.login(user, PIN, "vecino")
        return client

    def admin(self):
        client = ApiClient(self.api)
        client.login(ADMIN, ADMIN_PASS, "admin")
        return client

    def verified_email(self, customer_id=801, email=EMAIL):
        self.store.customers[customer_id] = replace(self.store.customers[customer_id], email=email,
                                                    email_verified_at=WEDNESDAY)

    def notices_of(self, customer_id):
        status, body, _ = self.client(customer_id).get("/api/avisos")
        self.assertEqual(status, 200, body)
        return body["avisos"]

    def kinds(self, customer_id):
        return [n["tipo"] for n in self.notices_of(customer_id)]

    def order_week(self, verify=True):
        for customer_id in WEEK:
            self.assertEqual(self.client(customer_id).post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})[0], 201)
        if verify:
            admin = self.admin()
            for order_id in range(1, 9):
                self.assertEqual(admin.post(f"/api/admin/pedidos/{order_id}/verificar")[0], 200)

    def deliver_week(self):
        self.order_week()
        self.clock[0] = SATURDAY
        admin = self.admin()
        for order_id in range(1, 9):
            self.assertEqual(admin.post("/api/admin/bolsas", {"pedido": order_id, "foto": f"b{order_id}.jpg"})[0], 200)
        return admin

    def delivered(self):
        admin = self.deliver_week()
        status, body, _ = admin.post("/api/admin/entregas", {"ciclo": "2026-W38", "zona": SAN_FELIPE,
                                                             "foto": "entrega.jpg", "recibe": "Sr. Ramos"})
        self.assertEqual(status, 200, body)
        return admin


class NoticeFlowTests(AvisosBase):
    # AV-A
    def test_av_a_pago_verificado(self):
        self.assertEqual(self.client(101).post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})[0], 201)
        self.assertEqual(self.notices_of(101), [])
        self.assertEqual(self.admin().post("/api/admin/pedidos/1/verificar")[0], 200)
        client = self.client(101)
        status, body, _ = client.get("/api/avisos")
        self.assertEqual((status, body["sin_leer"], [n["tipo"] for n in body["avisos"]]), (200, 1, ["PAGO_VERIFICADO"]))
        self.assertFalse(body["avisos"][0]["leido"])
        self.assertIn("pedido 1", body["avisos"][0]["texto"])
        self.assertEqual(client.get("/api/sesion")[1]["avisos_sin_leer"], 1)

    # AV-B
    def test_av_b_solo_el_dueno(self):
        self.order_week()
        self.assertEqual(self.kinds(801), ["PAGO_VERIFICADO"])
        self.assertEqual(self.kinds(101), [])
        mine = self.notices_of(802)
        self.assertEqual([n["tipo"] for n in mine], ["PAGO_VERIFICADO"])
        self.assertIn("pedido 2", mine[0]["texto"])

    # AV-C
    def test_av_c_entrega(self):
        self.delivered()
        for customer_id in WEEK:
            with self.subTest(vecino=customer_id):
                self.assertEqual(self.kinds(customer_id), ["ENTREGADO", "PAGO_VERIFICADO"])

    # AV-D
    def test_av_d_liquidacion(self):
        admin = self.delivered()
        status, result, _ = admin.post("/api/admin/ciclos/2026-W38/liquidar")
        self.assertEqual(status, 200, result)
        first = next(n for n in self.notices_of(801) if n["tipo"] == "LIQUIDADO")
        order = next(o for o in result["pedidos"] if o["id"] == 1)
        self.assertIn("2026-W38", first["texto"] + first["titulo"])
        self.assertIn(f"S/ {order['pagado']}", first["texto"])
        self.assertIn(f"S/ {order['costo']}", first["texto"])
        if D(order["devuelto"]) > 0:
            self.assertIn(f"S/ {order['devuelto']}", first["texto"])
        for customer_id in WEEK:
            self.assertIn("LIQUIDADO", self.kinds(customer_id))

    def test_av_d_un_pedido_cancelado_por_el_vecino_no_avisa(self):
        self.store.add_customer(Customer(809, "Vecino 809", SAN_FELIPE))
        set_pin(self.store, 809, PIN)
        self.assertEqual(self.client(801).post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})[0], 201)
        self.assertEqual(self.client(801).post("/api/pedidos/1/cancelar", {"destino": "SALDO"})[0], 200)
        for customer_id in WEEK[1:] + [809]:
            self.assertEqual(self.client(customer_id).post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})[0], 201)
        admin = self.admin()
        for order_id in range(2, 10):
            self.assertEqual(admin.post(f"/api/admin/pedidos/{order_id}/verificar")[0], 200)
        self.clock[0] = SATURDAY
        admin = self.admin()
        for order_id in range(2, 10):
            self.assertEqual(admin.post("/api/admin/bolsas", {"pedido": order_id, "foto": f"b{order_id}.jpg"})[0], 200)
        admin.post("/api/admin/entregas", {"ciclo": "2026-W38", "zona": SAN_FELIPE, "foto": "e.jpg", "recibe": "Sr. Ramos"})
        self.assertEqual(admin.post("/api/admin/ciclos/2026-W38/liquidar")[0], 200)
        self.assertNotIn("LIQUIDADO", self.kinds(801))
        self.assertIn("LIQUIDADO", self.kinds(802))

    # AV-E
    def test_av_e_entrega_fallida(self):
        admin = self.deliver_week()
        status, body, _ = admin.post("/api/admin/entregas-fallidas", {"ciclo": "2026-W38", "zona": SAN_FELIPE,
                                                                        "foto": "x.jpg", "motivo": "NADIE_RECIBE"})
        self.assertEqual(status, 200, body)
        for customer_id in WEEK:
            self.assertIn("NO_ENTREGADO", self.kinds(customer_id))
            self.assertNotIn("ENTREGADO", self.kinds(customer_id))

    # AV-F
    def test_av_f_reclamos(self):
        admin = self.delivered()
        for customer_id, product in ((801, "PAPA-AMARILLA"), (802, "PAPA-BLANCA")):
            status, body, _ = self.client(customer_id).post("/api/reclamos", {
                "pedido": customer_id - 800, "producto": product, "cantidad": "1", "motivo": "DANADO", "foto": "r.jpg"})
            self.assertEqual(status, 201, body)
        self.assertEqual(admin.post("/api/admin/ciclos/2026-W38/liquidar")[0], 200)
        status, approved, _ = admin.post("/api/admin/reclamos/1/revisar", {"decision": "aprobar"})
        self.assertEqual(status, 200, approved)
        self.assertEqual(admin.post("/api/admin/reclamos/2/revisar", {"decision": "rechazar"})[0], 200)
        first = next(n for n in self.notices_of(801) if n["tipo"] == "RECLAMO_APROBADO")
        self.assertIn(f"S/ {approved['devuelto']}", first["texto"])
        self.assertIn("RECLAMO_RECHAZADO", self.kinds(802))
        self.assertNotIn("RECLAMO_APROBADO", self.kinds(802))

    # AV-G
    def test_av_g_devolucion_pagada(self):
        self.order_week()
        self.assertEqual(self.client(801).post("/api/pedidos/1/cancelar", {"destino": "SALDO"})[0], 200)
        client = self.client(801)
        self.assertEqual(client.post("/api/saldo/devolucion", {"monto": "10.00"})[0], 200)
        refund = self.admin().get("/api/admin/devoluciones")[1]["devoluciones"][0]
        status, body, _ = self.admin().post(f"/api/admin/devoluciones/{refund['id']}/pagar", {"codigo": "OP-123"})
        self.assertEqual(status, 200, body)
        paid = next(n for n in self.notices_of(801) if n["tipo"] == "DEVOLUCION_PAGADA")
        self.assertIn("S/ 10.00", paid["texto"] + paid["titulo"])


class UnionNoticeTests(AvisosBase):
    def setUp(self):
        super().setUp()
        self.marta = 950
        self.store.add_customer(Customer(self.marta, "Marta Quispe", ARENALES))
        set_pin(self.store, self.marta, PIN)
        self.store.zones[ARENALES].admin_id = self.marta
        self.store.zones[ALAMOS].admin_id = 101
        self.store.zones[ARENALES].reception_accepted = True

    def request_union(self):
        status, body, _ = self.client(self.marta).post(f"/api/zonas/{ARENALES}/unir", {"destino": ALAMOS})
        self.assertEqual(status, 200, body)
        return body["solicitud"]

    # AV-H
    def test_av_h_union_solicitada_y_respondida(self):
        merge_id = self.request_union()
        asked = self.notices_of(101)
        self.assertEqual([n["tipo"] for n in asked], ["UNION_SOLICITADA"])
        self.assertIn("Edificio Arenales", asked[0]["titulo"])
        self.assertEqual(self.notices_of(self.marta), [])
        self.assertEqual(self.client(101).post(f"/api/solicitudes/{merge_id}/aceptar")[0], 200)
        self.assertEqual(self.kinds(self.marta), ["UNION_ACEPTADA"])
        self.assertEqual(self.kinds(101), ["UNION_SOLICITADA"])
        for bystander in (801, 802):
            self.assertEqual(self.kinds(bystander), [])

    def test_av_h_union_rechazada(self):
        merge_id = self.request_union()
        self.assertEqual(self.client(101).post(f"/api/solicitudes/{merge_id}/rechazar")[0], 200)
        self.assertEqual(self.kinds(self.marta), ["UNION_RECHAZADA"])

    def test_av_h_una_union_que_falla_no_avisa(self):
        self.clock[0] = datetime(2026, 9, 17, 10, 0, tzinfo=LIMA)  # jueves: ciclo cerrado
        status, _, _ = self.client(self.marta).post(f"/api/zonas/{ARENALES}/unir", {"destino": ALAMOS})
        self.assertEqual(status, 422)
        self.assertEqual(self.notices_of(101), [])

    def test_av_m_union_solicitada_manda_correo_al_admin(self):
        self.verified_email(101, "ana@gmail.com")
        self.request_union()
        self.assertEqual([m[0] for m in self.mailer.sent], ["ana@gmail.com"])


class ReadingTests(AvisosBase):
    def setUp(self):
        super().setUp()
        self.order_week()

    # AV-I
    def test_av_i_leer_uno(self):
        client = self.client(801)
        notice = client.get("/api/avisos")[1]["avisos"][0]
        status, body, _ = client.post("/api/avisos/leer", {"id": notice["id"]})
        self.assertEqual(status, 200, body)
        after = client.get("/api/avisos")[1]
        self.assertEqual((after["sin_leer"], after["avisos"][0]["leido"]), (0, True))
        self.assertEqual(client.post("/api/avisos/leer", {"id": notice["id"]})[0], 200)  # leer otra vez no cambia nada

    def test_av_i_leer_uno_deja_los_otros_sin_leer(self):
        for _ in range(2):
            notices.add(self.store, 801, "PAGO_VERIFICADO", "Otro", "Texto", self.clock[0])
        client = self.client(801)
        before = client.get("/api/avisos")[1]
        self.assertEqual(before["sin_leer"], 3)
        client.post("/api/avisos/leer", {"id": before["avisos"][0]["id"]})
        self.assertEqual(client.get("/api/avisos")[1]["sin_leer"], 2)

    # AV-J
    def test_av_j_leer_todos(self):
        notices.add(self.store, 801, "PAGO_VERIFICADO", "Otro", "Texto", self.clock[0])
        client = self.client(801)
        self.assertEqual(client.post("/api/avisos/leer", {})[0], 200)
        self.assertEqual(client.get("/api/avisos")[1]["sin_leer"], 0)
        self.assertEqual(client.get("/api/sesion")[1]["avisos_sin_leer"], 0)
        self.assertEqual(self.client(802).get("/api/avisos")[1]["sin_leer"], 1)  # los de otro no se tocan

    # AV-K
    def test_av_k_ajeno_o_inexistente(self):
        other = self.client(802).get("/api/avisos")[1]["avisos"][0]["id"]
        client = self.client(801)
        for notice_id in (other, 9999):
            with self.subTest(id=notice_id):
                status, body, _ = client.post("/api/avisos/leer", {"id": notice_id})
                self.assertEqual((status, body["error"]["codigo"]), (422, "NOTICE_NOT_FOUND"))
        self.assertEqual(self.client(802).get("/api/avisos")[1]["sin_leer"], 1)

    def test_av_k_id_que_no_es_numero(self):
        status, body, _ = self.client(801).post("/api/avisos/leer", {"id": "abc"})
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_INPUT"))

    # AV-L
    def test_av_l_tope_de_cincuenta(self):
        for number in range(55):
            notices.add(self.store, 801, "PAGO_VERIFICADO", f"Aviso {number}", "Texto", WEDNESDAY + timedelta(minutes=number))
        mine = self.client(801).get("/api/avisos")[1]["avisos"]
        self.assertEqual(len(mine), 50)
        self.assertEqual(mine[0]["titulo"], "Aviso 54")
        self.assertNotIn("Aviso 4", [n["titulo"] for n in mine])
        self.assertEqual(len(self.client(802).get("/api/avisos")[1]["avisos"]), 1)  # el tope es por vecino


class EmailNoticeTests(AvisosBase):
    # AV-M
    def test_av_m_correo_de_entrega(self):
        self.verified_email(801)
        self.delivered()
        sent = [m for m in self.mailer.sent if m[0] == EMAIL]
        self.assertEqual(len(sent), 1)
        delivered = next(n for n in self.notices_of(801) if n["tipo"] == "ENTREGADO")
        self.assertEqual(sent[0][1], delivered["titulo"])
        self.assertIn(delivered["texto"], sent[0][2])
        self.assertIn("Mi cuenta", sent[0][2])  # AV-09: cómo apagarlos

    # AV-N
    def test_av_n_sin_correo_verificado(self):
        self.store.customers[801] = replace(self.store.customers[801], email=EMAIL)  # sin verificar
        self.delivered()
        self.assertEqual(self.mailer.sent, [])
        self.assertIn("ENTREGADO", self.kinds(801))

    # AV-O
    def test_av_o_apagado_y_encendido(self):
        self.verified_email(801)
        client = self.client(801)
        self.assertEqual(client.post("/api/avisos/preferencias", {"avisos_correo": False})[0], 200)
        self.assertFalse(client.get("/api/avisos")[1]["correo_avisos"])
        self.assertFalse(client.get("/api/sesion")[1]["correo_avisos"])
        self.delivered()
        self.assertEqual(self.mailer.sent, [])
        self.assertIn("ENTREGADO", self.kinds(801))
        self.assertEqual(self.client(801).post("/api/avisos/preferencias", {"avisos_correo": True})[0], 200)
        self.assertTrue(self.client(801).get("/api/avisos")[1]["correo_avisos"])
        self.admin().post("/api/admin/ciclos/2026-W38/liquidar")
        self.assertEqual([m[0] for m in self.mailer.sent], [EMAIL])  # el de entrega no se manda a destiempo

    def test_av_o_la_preferencia_es_un_si_o_no(self):
        status, body, _ = self.client(801).post("/api/avisos/preferencias", {"avisos_correo": ["x"]})
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_INPUT"))

    # AV-P
    def test_av_p_pago_verificado_no_manda_correo(self):
        self.verified_email(801)
        self.order_week()
        self.assertEqual(self.kinds(801), ["PAGO_VERIFICADO"])
        self.assertEqual(self.mailer.sent, [])

    # AV-Q
    def test_av_q_una_sola_vez(self):
        self.verified_email(801)
        admin = self.delivered()
        self.assertEqual(len(self.mailer.sent), 1)
        admin.post("/api/admin/ciclos/2026-W38/liquidar")
        self.client(801).get("/api/avisos")
        self.client(801).post("/api/avisos/leer", {})
        self.assertEqual([m[1] for m in self.mailer.sent].count(
            next(n for n in self.notices_of(801) if n["tipo"] == "ENTREGADO")["titulo"]), 1)

    # AV-R
    def test_av_r_correo_caido(self):
        self.verified_email(801)
        self.mailer.fail = True
        status, body, _ = self.delivered_status()
        self.assertEqual(status, 200, body)
        self.assertEqual((body["zona"], body["pedidos"]), (SAN_FELIPE, 8))
        self.assertIn("ENTREGADO", self.kinds(801))

    def delivered_status(self):
        admin = self.deliver_week()
        return admin.post("/api/admin/entregas", {"ciclo": "2026-W38", "zona": SAN_FELIPE, "foto": "e.jpg",
                                                   "recibe": "Sr. Ramos"})

    def test_av_r_un_correo_caido_no_se_reintenta(self):
        self.verified_email(801)
        self.mailer.fail = True
        admin = self.deliver_week()
        admin.post("/api/admin/entregas", {"ciclo": "2026-W38", "zona": SAN_FELIPE, "foto": "e.jpg", "recibe": "Sr. Ramos"})
        self.mailer.fail = False
        admin.post("/api/admin/ciclos/2026-W38/liquidar")
        sent_to_me = [m for m in self.mailer.sent if m[0] == EMAIL]
        self.assertEqual(len(sent_to_me), 1)  # solo el de liquidación; el de entrega fallido no vuelve a salir
        self.assertNotIn("llegó", sent_to_me[0][1])

    # AV-S
    def test_av_s_sin_secretos(self):
        self.verified_email(801)
        admin = self.delivered()
        admin.post("/api/admin/ciclos/2026-W38/liquidar")
        everything = repr(self.mailer.sent) + repr(self.notices_of(801))
        self.assertNotIn(PIN, everything)
        self.assertNotIn("YP-", everything)  # el código de pago del Yape

    def test_av_n_el_correo_se_revisa_otra_vez_al_enviar(self):
        self.verified_email(801)
        notices.add(self.store, 801, "ENTREGADO", "Tu pedido llegó a tu zona", "Texto", WEDNESDAY)
        self.store.customers[801] = replace(self.store.customers[801], email_verified_at=None)
        self.assertEqual(notices.claim_emails(self.store), [])
        self.assertEqual(self.mailer.sent, [])



class RolesTests(AvisosBase):
    # AV-T
    def test_av_t_roles(self):
        anonymous = ApiClient(self.api)
        for method, path in (("GET", "/api/avisos"), ("POST", "/api/avisos/leer"), ("POST", "/api/avisos/preferencias")):
            with self.subTest(sin_sesion=path):
                status, body, _ = anonymous.request(method, path, {}, with_csrf=False)
                self.assertEqual((status, body["error"]["codigo"]), (401, "LOGIN_REQUIRED"))
        admin = self.admin()
        for method, path in (("GET", "/api/avisos"), ("POST", "/api/avisos/leer"), ("POST", "/api/avisos/preferencias")):
            with self.subTest(admin=path):
                status, body, _ = admin.request(method, path, {})
                self.assertEqual((status, body["error"]["codigo"]), (403, "FORBIDDEN"))

    def test_av_t_sesion_del_admin_no_trae_avisos(self):
        self.assertNotIn("avisos_sin_leer", self.admin().get("/api/sesion")[1])


class PersistenceTests(AvisosBase):
    # AV-U
    def test_av_u_persistencia(self):
        self.verified_email(801)
        self.delivered()
        self.client(801).post("/api/avisos/leer", {})
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = os.path.join(folder.name, "yapa.db")
        persistence.save(self.store, path)
        loaded = persistence.load(path)
        again = create_api(loaded, clock=lambda: self.clock[0], mailer=FakeMailer(), background_mail=False)
        client = ApiClient(again)
        client.login(801, PIN, "vecino")
        body = client.get("/api/avisos")[1]
        self.assertEqual((body["sin_leer"], [n["tipo"] for n in body["avisos"]]), (0, ["ENTREGADO", "PAGO_VERIFICADO"]))
        self.assertEqual([n.email for n in loaded.notices if n.kind == "ENTREGADO"][:1], ["ENVIADO"])

    def test_av_u_los_nuevos_avisos_siguen_la_numeracion(self):
        self.order_week()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = os.path.join(folder.name, "yapa.db")
        persistence.save(self.store, path)
        loaded = persistence.load(path)
        new = notices.add(loaded, 801, "PAGO_VERIFICADO", "Nuevo", "Texto", WEDNESDAY)
        self.assertEqual(len({n.notice_id for n in loaded.notices}), len(loaded.notices))
        self.assertEqual(new.notice_id, max(n.notice_id for n in loaded.notices))


class FailureTests(AvisosBase):
    # AV-V
    def test_av_v_si_el_aviso_falla_la_accion_termina_igual(self):
        self.assertEqual(self.client(801).post("/api/pedidos", {"lineas": BASKET, "metodo": "YAPE"})[0], 201)
        with mock.patch("yapa_sdd.notices.add", side_effect=RuntimeError("falla al avisar")), \
                mock.patch("traceback.print_exc"):
            status, body, _ = self.admin().post("/api/admin/pedidos/1/verificar")
        self.assertEqual(status, 200, body)
        self.assertEqual(body["pago"], "VERIFICADO")
        self.assertEqual(self.notices_of(801), [])


if __name__ == "__main__":
    unittest.main()
