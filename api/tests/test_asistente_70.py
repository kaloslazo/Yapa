"""Iteración 70 · Asistente de compra. Spec: docs/desarrollo/70-asistente-de-compra.md.
Ninguna prueba sale a internet: la IA es el proveedor falso de test_ia."""

import json

from api_client import ApiClient
from test_ia import Falso
from test_personal_por_rol import ADMIN, ADMIN_PASS, PIN, Base
from test_settlement import NOW

from datetime import timedelta
from decimal import Decimal as D

from yapa_sdd import assistant, ia
from yapa_sdd.order_registration import quote_order, register_order
from yapa_sdd.settlement import CycleSettlement, SettledOrder
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.web.api import create_api

FREE = "¿Me conviene pedir más limón esta semana?"


class AssistantTests(Base):
    def setUp(self):
        super().setUp()
        set_pin(self.store, self.first.customer_id, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.fake = Falso(groq={"respuesta": "Sí: el limón está a buen precio y tu grupo ya llegó."})
        self.ai = ia.AIClient([ia.Provider("groq", ia.GROQ_URL, "k", "texto")], post=self.fake)

    def client(self, ai="default"):
        api = create_api(self.store, clock=lambda: NOW, security_clock=lambda: NOW, ai=self.ai if ai == "default" else ai)
        neighbor = ApiClient(api)
        self.assertEqual(neighbor.login(self.first.customer_id, PIN)[0], 200)
        return neighbor

    def ask(self, question, ai="default", neighbor=None):
        status, data, _ = (neighbor or self.client(ai)).post("/api/asistente", {"pregunta": question})
        self.assertEqual(status, 200, data)
        return data

    # AS-A
    def test_as_a_order_status_from_data(self):
        data = self.ask("¿Dónde está mi pedido?")
        self.assertEqual((data["tema"], data["fuente"]), ("pedido", "datos"))
        self.assertIn(str(self.first.order_id), data["respuesta"])
        self.assertEqual(self.fake.enviados, [])

    # AS-B
    def test_as_b_price(self):
        data = self.ask("¿Cuánto cuesta la papa amarilla?")
        self.assertEqual((data["tema"], data["fuente"]), ("precio", "datos"))
        self.assertIn("Papa amarilla", data["respuesta"])
        self.assertIn("S/", data["respuesta"])

    # AS-C
    def test_as_c_savings(self):
        data = self.ask("¿Cuánto ahorré?")
        self.assertEqual(data["tema"], "ahorro")
        self.assertIn("saldo", data["respuesta"])

    # AS-D
    def test_as_d_group(self):
        data = self.ask("¿Cuántos faltan para el mínimo?")
        self.assertEqual(data["tema"], "grupo")
        self.assertIn("8 de 8", data["respuesta"])

    # AS-E
    def test_as_e_delivery(self):
        data = self.ask("¿Cuándo llega?")
        self.assertEqual(data["tema"], "entrega")
        self.assertIn("sábado 19/09", data["respuesta"])

    # AS-F
    def test_as_f_other_questions_go_to_ai_with_only_my_data(self):
        data = self.ask(FREE)
        self.assertEqual(data["fuente"], "ia")
        self.assertIn("limón", data["respuesta"])
        sent = json.dumps(self.fake.enviados[0], ensure_ascii=False)
        self.assertIn(f"Vecino {self.first.customer_id}", sent)
        self.assertNotIn(f"Vecino {self.orders[1].customer_id}", sent)

    # AS-G
    def test_as_g_without_ai_suggests_what_can_be_asked(self):
        data = self.ask(FREE, ai=None)
        self.assertEqual(data["fuente"], "sin_respuesta")
        self.assertTrue(data["sugerencias"])

    # AS-H
    def test_as_h_daily_ai_limit(self):
        neighbor = self.client()
        for _ in range(10):
            self.assertEqual(self.ask(FREE, neighbor=neighbor)["fuente"], "ia")
        self.assertEqual(self.ask(FREE, neighbor=neighbor)["fuente"], "sin_respuesta")
        self.assertEqual(len(self.fake.enviados), 10)
        self.assertEqual(self.ask("¿Dónde está mi pedido?", neighbor=neighbor)["fuente"], "datos")

    # AS-I
    def test_as_i_empty_question(self):
        status, data, _ = self.client().post("/api/asistente", {"pregunta": "   "})
        self.assertEqual(status, 422)
        self.assertEqual(data["error"]["codigo"], "QUESTION_REQUIRED")

    # AS-J
    def test_as_j_team_cannot_use_it(self):
        api = create_api(self.store, clock=lambda: NOW, security_clock=lambda: NOW, ai=self.ai)
        admin = ApiClient(api)
        self.assertEqual(admin.login(ADMIN, ADMIN_PASS, "admin")[0], 200)
        self.assertEqual(admin.post("/api/asistente", {"pregunta": "hola"})[0], 403)


class AssistantFixesTests(Base):
    def setUp(self):
        super().setUp()
        set_pin(self.store, self.first.customer_id, PIN)

    # AS-L
    def test_as_l_last_saving_is_the_latest_week(self):
        older = register_order(self.store, customer_id=self.first.customer_id, lines=[("PAPA-AMARILLA", "10"), ("CEBOLLA-ROJA", "10")],
                               payment_method="YAPE", operation_code="OLD", now=NOW - timedelta(days=7),
                               amount=quote_order(self.store, [("PAPA-AMARILLA", "10"), ("CEBOLLA-ROJA", "10")]).total)
        self.assertGreater(older.order_id, self.first.order_id)
        for order, cycle_id, refund in ((self.first, self.first.cycle, "3.00"), (older, older.cycle, "1.00")):
            order.status = "LIQUIDADO"
            settled = SettledOrder(order.order_id, "LIQUIDADO", paid=order.total, final_amount=order.total, refund_amount=D(refund))
            self.store.settlements[cycle_id] = CycleSettlement(cycle_id, {order.order_id: settled}, {}, D("0"), D("0"))
        text = assistant.answer(self.store, None, self.first.customer_id, "¿Cuánto ahorré?", NOW,
                                {"verificados": 8, "minimo": 8})["respuesta"]
        self.assertIn(f"pedido {self.first.order_id}", text)

    # AS-M
    def test_as_m_low_reasoning_and_rules_for_gpt_oss(self):
        fake = Falso(groq={"respuesta": "Con Yape o Plin."})
        ai = ia.AIClient([ia.Provider("groq", ia.GROQ_URL, "k", "openai/gpt-oss-120b")], post=fake)
        assistant.answer(self.store, ai, self.first.customer_id, "¿Puedo pagar con tarjeta?", NOW, {"verificados": 8, "minimo": 8})
        self.assertEqual(fake.enviados[0]["reasoning_effort"], "low")
        self.assertIn("Yape o Plin", json.dumps(fake.enviados[0], ensure_ascii=False))
