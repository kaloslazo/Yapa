"""Envío de correos (iteración 40, S-208). Docs: docs/desarrollo/40-correo-y-recuperar-pin.md.

Sin credenciales el motor imprime el mensaje en su consola (solo desarrollo y demo).
Con YAPA_SMTP_USER y YAPA_SMTP_PASSWORD (contraseña de aplicación de una cuenta Gmail de Yapa) manda por SMTP.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from . import mail_html


class MailError(Exception):
    """No se pudo enviar el correo."""


class ConsoleMailer:
    def send(self, to: str, subject: str, body: str) -> None:
        print(f"[correo a {to}] {subject}\n{body}", flush=True)


class SmtpMailer:
    def __init__(self, host: str, port: int, user: str, password: str, sender: str = "", app_url: str = ""):
        self.host, self.port, self.user, self.password = host, port, user, password
        self.sender = sender or user
        self.app_url = app_url

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = f"Yapa <{self.sender}>", to, subject
        message.set_content(body)
        message.add_alternative(mail_html.render(subject, body, self.app_url), subtype="html")  # S-222
        try:
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as error:
            raise MailError(str(error)) from error


def mailer_from_env(env=None):
    env = os.environ if env is None else env
    user, password = env.get("YAPA_SMTP_USER", ""), env.get("YAPA_SMTP_PASSWORD", "")
    if not (user and password):
        return ConsoleMailer()
    return SmtpMailer(env.get("YAPA_SMTP_HOST", "smtp.gmail.com"), int(env.get("YAPA_SMTP_PORT", "587")), user, password,
                      env.get("YAPA_SMTP_FROM", ""), env.get("YAPA_PUBLIC_URL", ""))
