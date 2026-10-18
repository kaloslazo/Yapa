"""Iteración 40: correo obligatorio y recuperar el PIN con un código (docs/desarrollo/40-correo-y-recuperar-pin.md)."""

from contextlib import redirect_stdout
from datetime import datetime, timedelta
from dataclasses import replace
import io
import json
import re
import unittest

from api_client import ApiClient
from test_api import ADMIN, ADMIN_PASS, PIN, WEDNESDAY
from web_client import fast_hashing

from yapa_sdd.auth import MAX_FAILURES, set_admin_password, set_pin
from yapa_sdd.mailer import ConsoleMailer, MailError
from yapa_sdd.seed import pilot_store
from yapa_sdd.web.api import create_api

EMAIL = "ana@gmail.com"
NEW_PIN = "135790"
GENERIC = "Si tu número está registrado"


class FakeMailer:
    def __init__(self):
        self.sent = []
        self.fail = False

    def send(self, to, subject, body):
        if self.fail:
            raise MailError("sin conexión")
        self.sent.append((to, subject, body))

    def last_code(self):
        return re.search(r"\b(\d{6})\b", self.sent[-1][2]).group(1)


class AccountBase(unittest.TestCase):
    def setUp(self):
        fast_hashing(self)
        self.store = pilot_store()
        self.store.customers[101] = replace(self.store.customers[101], phone="987654321")
        set_pin(self.store, 101, PIN)
        set_pin(self.store, 104, "246802")
        set_admin_password(self.store, ADMIN, ADMIN_PASS)
        self.clock = [WEDNESDAY]
        self.mailer = FakeMailer()
        self.api = create_api(self.store, clock=lambda: self.clock[0], mailer=self.mailer)

    def neighbor(self, customer_id=101, pin=PIN):
        client = ApiClient(self.api)
        client.login(customer_id, pin, "vecino")
        return client

    def admin(self):
        client = ApiClient(self.api)
        client.login(ADMIN, ADMIN_PASS, "admin")
        return client

    def anonymous(self, path, body):
        return ApiClient(self.api).post(path, body, with_csrf=False)

    def verify_email(self, customer_id=101, email=EMAIL, pin=PIN):
        client = self.neighbor(customer_id, pin)
        self.assertEqual(client.post("/api/cuenta/correo", {"correo": email})[0], 200)
        status, body, _ = client.post("/api/cuenta/correo/verificar", {"codigo": self.mailer.last_code()})
        self.assertEqual(status, 200, body)
        self.clock[0] += timedelta(minutes=2)
        return client

    def open_pin_requests(self):
        return self.admin().get("/api/admin/pin-solicitudes")[1]["solicitudes"]

    def register(self, **fields):
        data = {"nombre": "Vecino Nuevo", "celular": "955111222", "zona": "Z-LINCE-01", "consentimiento": True,
                "correo": "nuevo@gmail.com"} | fields
        return self.admin().post("/api/admin/vecinos", {k: v for k, v in data.items() if v is not None})


class RegistrationTests(AccountBase):
    # CR-A
    def test_cr_a_alta_sin_correo(self):
        status, body, _ = self.register(correo=None)
        self.assertEqual((status, body["error"]["codigo"]), (422, "EMAIL_REQUIRED"))

    # CR-B
    def test_cr_b_formato(self):
        for bad in ("ana@", "a b@x.com", "a" * 116 + "@x.com", "sin-arroba.com"):
            status, body, _ = self.register(correo=bad)
            self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_EMAIL"), bad)

    # CR-C
    def test_cr_c_unico_sin_importar_mayusculas(self):
        self.assertEqual(self.register(correo="Repetido@Gmail.com")[0], 201)
        status, body, _ = self.register(correo="repetido@gmail.COM", celular="955111333")
        self.assertEqual((status, body["error"]["codigo"]), (422, "EMAIL_ALREADY_REGISTERED"))

    # CR-D
    def test_cr_d_se_guarda_en_minusculas_y_sin_verificar(self):
        status, body, _ = self.register(correo="Ana@Gmail.com")
        self.assertEqual(status, 201, body)
        customer = self.store.customers[body["id"]]
        self.assertEqual((customer.email, customer.email_verified_at), ("ana@gmail.com", None))


class VerificationTests(AccountBase):
    # CR-E
    def test_cr_e_agregar_correo_manda_un_codigo(self):
        status, body, _ = self.neighbor().post("/api/cuenta/correo", {"correo": EMAIL})
        self.assertEqual((status, body), (200, {"enviado": True}))
        to, _, text = self.mailer.sent[-1]
        self.assertEqual(to, EMAIL)
        self.assertRegex(text, r"\b\d{6}\b")

    # CR-F
    def test_cr_f_verificar(self):
        client = self.verify_email()
        status, body, _ = client.get("/api/sesion")
        self.assertEqual((body["correo"], body["correo_verificado"]), ("a***@gmail.com", True))

    # CR-G
    def test_cr_g_codigo_malo(self):
        client = self.neighbor()
        client.post("/api/cuenta/correo", {"correo": EMAIL})
        status, body, _ = client.post("/api/cuenta/correo/verificar", {"codigo": "000000"})
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_CODE"))
        self.assertFalse(client.get("/api/sesion")[1]["correo_verificado"])

    # CR-H
    def test_cr_h_se_agota_a_los_cinco_intentos(self):
        client = self.neighbor()
        client.post("/api/cuenta/correo", {"correo": EMAIL})
        good = self.mailer.last_code()
        wrong = "000000" if good != "000000" else "111111"
        for _ in range(5):
            client.post("/api/cuenta/correo/verificar", {"codigo": wrong})
        status, body, _ = client.post("/api/cuenta/correo/verificar", {"codigo": good})
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_CODE"))

    # CR-I
    def test_cr_i_vence_a_los_diez_minutos(self):
        client = self.neighbor()
        client.post("/api/cuenta/correo", {"correo": EMAIL})
        self.clock[0] += timedelta(minutes=11)
        client = self.neighbor()
        status, body, _ = client.post("/api/cuenta/correo/verificar", {"codigo": self.mailer.last_code()})
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_CODE"))

    # CR-J
    def test_cr_j_reenvio_muy_pronto(self):
        client = self.neighbor()
        client.post("/api/cuenta/correo", {"correo": EMAIL})
        self.clock[0] += timedelta(seconds=30)
        status, body, _ = self.neighbor().post("/api/cuenta/correo", {"correo": EMAIL})
        self.assertEqual((status, body["error"]["codigo"]), (422, "EMAIL_CODE_TOO_SOON"))

    # CR-K
    def test_cr_k_tope_por_hora(self):
        for _ in range(5):
            self.assertEqual(self.neighbor().post("/api/cuenta/correo", {"correo": EMAIL})[0], 200)
            self.clock[0] += timedelta(seconds=61)
        status, body, _ = self.neighbor().post("/api/cuenta/correo", {"correo": EMAIL})
        self.assertEqual((status, body["error"]["codigo"]), (422, "EMAIL_CODE_LIMIT"))

    # CR-V (con sesión)
    def test_cr_v_falla_el_envio_con_sesion(self):
        self.mailer.fail = True
        status, body, _ = self.neighbor().post("/api/cuenta/correo", {"correo": EMAIL})
        self.assertEqual((status, body["error"]["codigo"]), (422, "EMAIL_SEND_FAILED"))

    # CR-W
    def test_cr_w_roles(self):
        status, body, _ = ApiClient(self.api).post("/api/cuenta/correo", {"correo": EMAIL}, with_csrf=False)
        self.assertEqual((status, body["error"]["codigo"]), (401, "LOGIN_REQUIRED"))
        status, body, _ = self.admin().post("/api/cuenta/correo", {"correo": EMAIL})
        self.assertEqual((status, body["error"]["codigo"]), (403, "FORBIDDEN"))

    # CR-Y
    def test_cr_y_cambiar_el_correo_pierde_la_verificacion(self):
        client = self.verify_email()
        client.post("/api/cuenta/correo", {"correo": "otro@gmail.com"})
        self.assertFalse(client.get("/api/sesion")[1]["correo_verificado"])
        self.mailer.sent.clear()
        self.anonymous("/api/pin/olvide", {"usuario": "101"})
        self.assertEqual(self.mailer.sent, [])
        self.assertEqual(len(self.open_pin_requests()), 1)


class RecoveryTests(AccountBase):
    def ask(self, user="101"):
        return self.anonymous("/api/pin/olvide", {"usuario": user})

    def reset(self, user="101", code=None, pin=NEW_PIN):
        return self.anonymous("/api/pin/restablecer", {"usuario": user, "codigo": code or self.mailer.last_code(), "pin": pin})

    def login(self, pin, user="101"):
        return ApiClient(self.api).post("/api/sesion", {"tipo": "vecino", "usuario": user, "secreto": pin}, with_csrf=False)[0]

    # CR-L
    def test_cr_l_olvide_con_correo_verificado(self):
        self.verify_email()
        self.mailer.sent.clear()
        status, body, _ = self.ask()
        self.assertEqual(status, 200)
        self.assertIn(GENERIC, body["mensaje"])
        self.assertEqual(len(self.mailer.sent), 1)
        self.assertEqual(self.mailer.sent[0][0], EMAIL)
        self.assertEqual(self.open_pin_requests(), [])

    # CR-M
    def test_cr_m_olvide_sin_correo_verificado_va_al_equipo(self):
        status, body, _ = self.ask()
        self.assertEqual(status, 200)
        self.assertEqual(self.mailer.sent, [])
        self.assertEqual([r["cliente"] for r in self.open_pin_requests()], [101])

    # CR-N
    def test_cr_n_numero_que_no_existe(self):
        status, body, _ = self.ask("987654")
        self.assertEqual((status, GENERIC in body["mensaje"]), (200, True))
        self.assertEqual((self.mailer.sent, self.open_pin_requests()), ([], []))

    def same_answer(self):
        self.verify_email()
        self.mailer.sent.clear()
        a = self.ask("101")
        b = self.ask("987654")
        c = self.ask("104")
        self.assertEqual((a[0], a[1]), (b[0], b[1]))
        self.assertEqual((a[0], a[1]), (c[0], c[1]))

    def test_op_a_misma_respuesta_exista_o_no_ahora_con_correo(self):
        self.same_answer()

    # CR-O
    def test_cr_o_restablecer(self):
        self.verify_email()
        self.ask()
        status, body, _ = self.reset()
        self.assertEqual(status, 200, body)
        self.assertEqual(self.login(NEW_PIN), 200)
        self.assertNotEqual(self.login(PIN), 200)

    # CR-P
    def test_cr_p_quita_el_bloqueo(self):
        self.verify_email()
        for _ in range(MAX_FAILURES):
            self.login("999999")
        self.assertNotEqual(self.login(PIN), 200)
        self.clock[0] += timedelta(minutes=2)
        self.ask()
        self.assertEqual(self.reset()[0], 200)
        self.assertEqual(self.login(NEW_PIN), 200)

    # CR-Q
    def test_cr_q_el_codigo_se_gasta(self):
        self.verify_email()
        self.ask()
        code = self.mailer.last_code()
        self.assertEqual(self.reset(code=code)[0], 200)
        status, body, _ = self.reset(code=code, pin="864209")
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_CODE"))

    # CR-R
    def test_cr_r_los_errores_son_iguales(self):
        self.verify_email()
        answers = [self.reset(user="987654", code="123456"), self.reset(user="104", code="123456"),
                   self.reset(user="101", code="123456")]
        self.assertEqual({(s, b["error"]["codigo"], b["error"]["mensaje"]) for s, b, _ in answers},
                         {(422, "INVALID_CODE", answers[0][1]["error"]["mensaje"])})

    # CR-S
    def test_cr_s_pin_invalido_no_gasta_el_codigo(self):
        self.verify_email()
        self.ask()
        code = self.mailer.last_code()
        status, body, _ = self.reset(code=code, pin="12")
        self.assertEqual((status, body["error"]["codigo"]), (422, "INVALID_PIN"))
        self.assertEqual(self.reset(code=code)[0], 200)

    # CR-T
    def test_cr_t_cierra_la_cola_del_equipo(self):
        self.anonymous("/api/pin/olvide", {"usuario": "101"})  # sin correo: va a la cola
        self.assertEqual(len(self.open_pin_requests()), 1)
        self.verify_email()
        self.ask()
        self.assertEqual(self.reset()[0], 200)
        self.assertEqual(self.open_pin_requests(), [])

    # CR-U
    def test_cr_u_el_codigo_no_se_guarda_en_claro(self):
        client = self.verify_email()
        self.ask()
        code = self.mailer.last_code()
        saved = json.dumps({str(k): v for k, v in self.store.email_codes.items()}, default=str)
        self.assertNotIn(code, saved)
        for text in (json.dumps(client.get("/api/sesion")[1]), json.dumps(self.ask()[1])):
            self.assertNotIn(code, text)

    # CR-V (anónimo)
    def test_cr_v_falla_el_envio_sin_cambiar_la_respuesta(self):
        self.verify_email()
        normal = self.ask()
        self.clock[0] += timedelta(minutes=2)
        self.mailer.fail = True
        failing = self.ask()
        self.assertEqual((normal[0], normal[1]), (failing[0], failing[1]))

    # S-209
    def test_cr_k2_el_reenvio_anonimo_se_limita_en_silencio(self):
        self.verify_email()
        self.mailer.sent.clear()
        first = self.ask()
        again = self.ask()
        self.assertEqual((first[0], first[1]), (again[0], again[1]))
        self.assertEqual(len(self.mailer.sent), 1)


class ConsoleTests(unittest.TestCase):
    # CR-X
    def test_cr_x_sin_credenciales_el_codigo_sale_en_consola(self):
        out = io.StringIO()
        with redirect_stdout(out):
            ConsoleMailer().send("ana@gmail.com", "Tu código de Yapa", "Tu código es 482915.")
        self.assertIn("482915", out.getvalue())
        self.assertIn("ana@gmail.com", out.getvalue())


if __name__ == "__main__":
    unittest.main()
