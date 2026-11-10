"""Iteraciones 60 y 61 · IA: "Arma mi canasta" y ayuda para atención.

Specs: docs/desarrollo/60-arma-mi-canasta-ia.md y 61-atencion-con-ia.md. Ninguna prueba sale a internet: el envío
HTTP se reemplaza por un proveedor falso.
"""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
import unittest

from api_client import ApiClient
from test_settlement import CYCLE, NOW, Scenario
from web_client import fast_hashing

from yapa_sdd import ia, incidents, partners
from yapa_sdd.auth import set_admin_password, set_pin
from yapa_sdd.claims import Claim
from yapa_sdd.cycle import LIMA
from yapa_sdd.domain import BusinessRuleError
from yapa_sdd.web.api import create_api


ADMIN, ADMIN_PASS, PIN, PASS = "admin-yapa", "yapa-admin-2026", "482915", "personal-2026"
ANA = 101
BASKET_JSON = {"lineas": [{"id": "PAPA-AMARILLA", "cantidad": 2.4}, {"id": "CEBOLLA-ROJA", "cantidad": 3},
                          {"id": "NO-EXISTE", "cantidad": 1}, {"id": "PAPA-AMARILLA", "cantidad": 1}],
               "comentario": "Para 4 personas"}


def respuesta(contenido) -> dict:
    texto = contenido if isinstance(contenido, str) else json.dumps(contenido)
    return {"choices": [{"message": {"content": texto}}]}


class Falso:
    """Proveedor falso: por nombre de proveedor devuelve una respuesta o lanza un error; guarda lo que recibió."""

    def __init__(self, **por_proveedor):
        self.por_proveedor = por_proveedor
        self.enviados = []

    def __call__(self, url, headers, body, timeout):
        self.enviados.append(body)
        nombre = "groq" if "groq" in url else "github"
        salida = self.por_proveedor[nombre]
        if isinstance(salida, Exception):
            raise salida
        return respuesta(salida)


def cliente(falso) -> ia.AIClient:
    return ia.AIClient([ia.Provider("groq", ia.GROQ_URL, "g", "m1"), ia.Provider("github", ia.GITHUB_URL, "h", "m2")],
                       post=falso)


def pedido_de(store, primer_cliente):
    """Un pedido verificado en Z-JM-01 sobre el mismo almacén."""
    s = Scenario()
    s.store, s.next_customer = store, primer_cliente
    return s.order("Z-JM-01")


class Base(unittest.TestCase):
    def setUp(self):
        self.store = Scenario().store
        self.store.customers[ANA] = replace(self.store.customers[ANA], phone="987654321", email="ana@correo.pe")

    def assertRule(self, expected, fn, *args, **kwargs):
        with self.assertRaises(BusinessRuleError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, expected)

    def sugerir(self, falso, texto="somos 4 y haré lomo saltado", now=NOW):
        return ia.suggest_basket(self.store, cliente(falso), ANA, texto, now)


class BasketSpecTests(Base):
    # IA-A
    def test_ia_a_suggestion_is_cleaned_and_priced_by_the_engine(self):
        sug = self.sugerir(Falso(groq=BASKET_JSON))
        lineas = {l["id"]: l for l in sug["lineas"]}
        self.assertEqual(set(lineas), {"PAPA-AMARILLA", "CEBOLLA-ROJA"})
        self.assertEqual((lineas["PAPA-AMARILLA"]["cantidad"], lineas["CEBOLLA-ROJA"]["cantidad"]), (D("4"), D("3")))
        catalogo = self.store.catalog_for(CYCLE)
        esperado = D("4") * catalogo["PAPA-AMARILLA"].max_unit_price() + D("3") * catalogo["CEBOLLA-ROJA"].max_unit_price()
        self.assertEqual(sug["subtotal"], esperado)
        self.assertEqual(sug["falta"], (D("50") - esperado).quantize(D("0.01"), rounding="ROUND_CEILING"))
        self.assertEqual((sug["comentario"], sug["proveedor"]), ("Para 4 personas", "groq"))

    # IA-B
    def test_ia_b_line_cap(self):
        sug = self.sugerir(Falso(groq={"lineas": [{"id": "PAPA-AMARILLA", "cantidad": 25}]}))
        self.assertEqual(sug["lineas"][0]["cantidad"], D("10"))

    # IA-C
    def test_ia_c_fallback(self):
        sug = self.sugerir(Falso(groq=ia.AIError("429 demasiadas consultas"), github=BASKET_JSON))
        self.assertEqual(sug["proveedor"], "github")
        sug = self.sugerir(Falso(groq="esto no es json", github=BASKET_JSON))
        self.assertEqual(sug["proveedor"], "github")
        self.assertRule("IA_UNAVAILABLE", self.sugerir, Falso(groq=ia.AIError("x"), github=ia.AIError("y")))

    # IA-D
    def test_ia_d_nothing_valid(self):
        self.assertRule("IA_EMPTY_SUGGESTION", self.sugerir, Falso(groq={"lineas": [{"id": "CAVIAR", "cantidad": 1}]}))

    # IA-E
    def test_ia_e_text_and_daily_limit(self):
        falso = Falso(groq=BASKET_JSON)
        self.assertRule("INVALID_INPUT", self.sugerir, falso, texto="ab")
        self.assertRule("INVALID_INPUT", self.sugerir, falso, texto="x" * 301)
        for _ in range(10):
            self.sugerir(falso)
        self.assertRule("IA_LIMIT", self.sugerir, falso)
        self.sugerir(falso, now=NOW + timedelta(days=1))

    # IA-G
    def test_ia_g_no_personal_data(self):
        falso = Falso(groq=BASKET_JSON)
        self.sugerir(falso)
        enviado = json.dumps(falso.enviados[0], ensure_ascii=False)
        for dato in ("Ana Torres", "987654321", "ana@correo.pe"):
            self.assertNotIn(dato, enviado)
        self.assertIn("PAPA-AMARILLA", enviado)

    # IA-H
    def test_ia_h_configuration(self):
        ambos = ia.from_env({"YAPA_GROQ_CLAVE": "g", "YAPA_GITHUB_MODELS_CLAVE": "h"})
        self.assertEqual([p.name for p in ambos.providers], ["groq", "github"])
        self.assertEqual(ambos.providers[0].model, "openai/gpt-oss-120b")
        self.assertEqual([p.name for p in ia.from_env({"YAPA_GITHUB_MODELS_CLAVE": "h"}).providers], ["github"])
        self.assertIsNone(ia.from_env({}))


class SupportSpecTests(Base):
    def setUp(self):
        super().setUp()
        self.order = pedido_de(self.store, 2000)
        self.store.claims[1] = Claim(1, self.order.order_id, self.order.customer_id, "CEBOLLA-ROJA", D("1"), "DANADO",
                                     "f.jpg", NOW)
        partners.create_staff(self.store, "atencion-1", partners.SUPPORT, "Atención", PASS, by=ADMIN, now=NOW)
        partners.create_staff(self.store, "armado-1", partners.PACKER, "Armado", PASS, by=ADMIN, now=NOW)

    def ayuda(self, falso, tipo="reclamo", registro=1, by="atencion-1"):
        return ia.suggest_support(self.store, cliente(falso), tipo, registro, by=by)

    # IA-I
    def test_ia_i_claim_suggestion_changes_nothing(self):
        sug = self.ayuda(Falso(groq={"categoria": "DANADO", "prioridad": "ALTA",
                                     "borrador": "Hola, sentimos que la cebolla llegó dañada."}))
        self.assertEqual((sug["categoria"], sug["prioridad"]), ("DANADO", "ALTA"))
        self.assertTrue(sug["borrador"].startswith("Hola"))
        self.assertEqual(self.store.claims[1].status, "PENDIENTE")

    # IA-J
    def test_ia_j_values_outside_the_list(self):
        sug = self.ayuda(Falso(groq={"categoria": "QUEJA", "prioridad": "URGENTE", "borrador": "x" * 700}))
        self.assertEqual((sug["categoria"], sug["prioridad"], len(sug["borrador"])), ("OTRO", "MEDIA", 600))
        self.assertRule("IA_EMPTY_SUGGESTION", self.ayuda, Falso(groq={"categoria": "OTRO", "borrador": "  "}))

    # IA-K
    def test_ia_k_no_personal_data(self):
        cliente_id = self.order.customer_id
        self.store.customers[cliente_id] = replace(self.store.customers[cliente_id], phone="912345678",
                                                   email="vecino@correo.pe")
        falso = Falso(groq={"categoria": "DANADO", "prioridad": "MEDIA", "borrador": "Hola"})
        self.ayuda(falso)
        enviado = json.dumps(falso.enviados[0], ensure_ascii=False)
        for dato in (self.store.customers[cliente_id].name, "912345678", "vecino@correo.pe"):
            self.assertNotIn(dato, enviado)
        self.assertIn("Cebolla roja", enviado)

    # IA-L
    def test_ia_l_roles_and_records(self):
        falso = Falso(groq={"categoria": "OTRO", "prioridad": "BAJA", "borrador": "Hola"})
        self.assertRule("NOT_AUTHORIZED", self.ayuda, falso, by="armado-1")
        self.assertRule("INVALID_INPUT", self.ayuda, falso, tipo="pedido")
        self.assertRule("CLAIM_NOT_FOUND", self.ayuda, falso, registro=999)
        self.assertRule("INCIDENT_NOT_FOUND", self.ayuda, falso, tipo="incidencia", registro=999)


class ApiTests(Base):
    def setUp(self):
        super().setUp()
        fast_hashing(self)
        set_pin(self.store, ANA, PIN)
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        partners.create_staff(self.store, "atencion-1", partners.SUPPORT, "Atención", PASS, by=ADMIN, now=NOW)
        partners.create_staff(self.store, "armado-1", partners.PACKER, "Armado", PASS, by=ADMIN, now=NOW)

    def login(self, api, user, secret, kind="vecino"):
        c = ApiClient(api)
        self.assertEqual(c.login(user, secret, kind)[0], 200)
        return c

    # IA-F
    def test_ia_f_disabled_without_keys(self):
        api = create_api(self.store, clock=lambda: NOW)
        self.assertFalse(ApiClient(api).get("/api/estado")[1]["ia"])
        vecina = self.login(api, ANA, PIN)
        status, data, _ = vecina.post("/api/canasta/sugerir", {"texto": "lomo saltado para 4"})
        self.assertEqual((status, data["error"]["codigo"]), (422, "IA_DISABLED"))

    # IA-A (API) e IA-M
    def test_ia_api_basket_and_support(self):
        falso = Falso(groq=BASKET_JSON)
        api = create_api(self.store, clock=lambda: NOW, ai=cliente(falso))
        self.assertTrue(ApiClient(api).get("/api/estado")[1]["ia"])
        vecina = self.login(api, ANA, PIN)
        status, data, _ = vecina.post("/api/canasta/sugerir", {"texto": "lomo saltado para 4"})
        self.assertEqual(status, 200)
        self.assertEqual([(l["id"], l["cantidad"]) for l in data["lineas"]], [("PAPA-AMARILLA", "4"), ("CEBOLLA-ROJA", "3")])
        self.assertIn("falta", data)
        self.assertEqual(data["proveedor"], "groq")

        incidents.open_incident(self.store, pedido_de(self.store, 3000).order_id, "ENTREGA",
                                "La portería dice que llegó tarde", by=ADMIN, now=NOW)
        falso.por_proveedor["groq"] = {"categoria": "ENTREGA", "prioridad": "BAJA", "borrador": "Hola, gracias por avisar."}
        atencion = self.login(api, "atencion-1", PASS, "atencion")
        status, data, _ = atencion.post("/api/admin/ia/atencion", {"tipo": "incidencia", "id": 1})
        self.assertEqual((status, data["categoria"]), (200, "ENTREGA"))
        armado = self.login(api, "armado-1", PASS, "armador")
        self.assertEqual(armado.post("/api/admin/ia/atencion", {"tipo": "incidencia", "id": 1})[0], 403)


if __name__ == "__main__":
    unittest.main()
