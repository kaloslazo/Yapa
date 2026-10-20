"""Iteración 43 · Correos con diseño. Spec: docs/desarrollo/43-correo-html.md."""

import contextlib
import io
import re
import unittest
from unittest import mock

from yapa_sdd import mail_html, mailer
from yapa_sdd.mailer import ConsoleMailer, SmtpMailer

CODE_BODY = ("Estás agregando este correo a tu cuenta de Yapa.\n\nTu código es 795704. Vale 10 minutos.\n"
             "Si no lo pediste tú, ignora este mensaje: nadie puede entrar a tu cuenta sin él.\n\nYapa")
NOTICE_BODY = ("Hola Ana,\n\nTu pedido llegó a tu zona.\n\nEntra a Yapa para ver el detalle.\n"
               "Si no quieres recibir estos correos, apágalos en Mi cuenta.\n\nYapa")


class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout=None):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        pass

    def send_message(self, message):
        FakeSMTP.sent.append(message)


def send_with(smtp_mailer, body, subject="Asunto de prueba"):
    FakeSMTP.sent = []
    with mock.patch.object(mailer.smtplib, "SMTP", FakeSMTP):
        smtp_mailer.send("vecino@example.com", subject, body)
    return FakeSMTP.sent[0]


def paragraphs(html):
    return [re.sub(r"<[^>]+>", "", text).strip() for text in re.findall(r"<p[^>]*>(.*?)</p>", html, re.S)]


class CorreoHtmlTest(unittest.TestCase):
    def setUp(self):
        self.smtp = SmtpMailer("smtp.example.com", 587, "usuario", "clave", "avisos@yapa.example")

    def test_ht_a_dos_versiones(self):
        message = send_with(self.smtp, NOTICE_BODY)
        plain = message.get_body(preferencelist=("plain",)).get_content()
        html = message.get_body(preferencelist=("html",)).get_content()
        self.assertEqual(plain.strip(), NOTICE_BODY)
        self.assertIn("<html", html.lower())

    def test_ht_b_cabeceras(self):
        message = send_with(self.smtp, NOTICE_BODY, subject="Tu pedido llegó")
        self.assertEqual(message["From"], "Yapa <avisos@yapa.example>")
        self.assertEqual(message["To"], "vecino@example.com")
        self.assertEqual(message["Subject"], "Tu pedido llegó")

    def test_ht_c_se_escapa(self):
        body = "Hola <b>Ana</b>,\n\n<script>alert(1)</script>\n\nYapa"
        html = mail_html.render("Asunto", body)
        self.assertNotIn("<script", html)
        self.assertNotIn("<b>Ana", html)
        self.assertIn("&lt;b&gt;Ana&lt;/b&gt;", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_ht_d_codigo_destacado(self):
        html = mail_html.render("Verifica tu correo en Yapa", CODE_BODY)
        self.assertEqual(html.count("795704"), 1)
        self.assertRegex(html, r'data-role="code"[^>]*>\s*795704\s*<')
        self.assertIn("10 minutos", html)

    def test_ht_e_sin_imagenes_ni_scripts(self):
        for body in (CODE_BODY, NOTICE_BODY):
            html = mail_html.render("Asunto", body).lower()
            for banned in ("<img", "<script", "<link", "@import", "http"):
                self.assertNotIn(banned, html)

    def test_ht_f_boton(self):
        html = mail_html.render("Asunto", NOTICE_BODY, app_url="https://yapa.example")
        self.assertRegex(html, r'<a [^>]*href="https://yapa\.example"[^>]*>\s*Abrir Yapa\s*</a>')

    def test_ht_g_boton_inseguro(self):
        for url in ("javascript:alert(1)", "ftp://yapa.example", ""):
            html = mail_html.render("Asunto", NOTICE_BODY, app_url=url)
            self.assertNotIn("Abrir Yapa", html)
            self.assertNotIn("javascript:", html)

    def test_ht_g_la_direccion_se_escapa(self):
        html = mail_html.render("Asunto", NOTICE_BODY, app_url='https://yapa.example/"><script>')
        self.assertNotIn("<script", html)

    def test_ht_h_aviso_con_pie(self):
        html = mail_html.render("Tu pedido llegó", NOTICE_BODY)
        self.assertIn("Tu pedido llegó a tu zona.", html)
        self.assertIn("apágalos en Mi cuenta", html)

    def test_ht_i_orden_y_despedida(self):
        body = "Hola Ana,\n\nUno.\n\nDos.\n\nTres.\n\nYapa"
        texts = paragraphs(mail_html.render("Asunto", body))
        self.assertEqual([t for t in texts if t in ("Hola Ana,", "Uno.", "Dos.", "Tres.")],
                         ["Hola Ana,", "Uno.", "Dos.", "Tres."])
        self.assertNotIn("Yapa", texts)

    def test_ht_j_consola_sigue_en_texto(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            ConsoleMailer().send("vecino@example.com", "Asunto", CODE_BODY)
        self.assertIn("795704", out.getvalue())
        self.assertNotIn("<html", out.getvalue().lower())

    def test_ht_k_variable_de_entorno(self):
        env = {"YAPA_SMTP_USER": "u", "YAPA_SMTP_PASSWORD": "p", "YAPA_PUBLIC_URL": "https://yapa.example"}
        message = send_with(mailer.mailer_from_env(env), NOTICE_BODY)
        self.assertIn("Abrir Yapa", message.get_body(preferencelist=("html",)).get_content())
        env.pop("YAPA_PUBLIC_URL")
        message = send_with(mailer.mailer_from_env(env), NOTICE_BODY)
        self.assertNotIn("Abrir Yapa", message.get_body(preferencelist=("html",)).get_content())


if __name__ == "__main__":
    unittest.main()
