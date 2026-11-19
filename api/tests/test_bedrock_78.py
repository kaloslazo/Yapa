"""Iteración 78 · Las fotos se leen con Claude en Bedrock (cuenta estudiantil). Spec: docs/desarrollo/78-fotos-con-bedrock.md.

Ninguna prueba sale a internet: Bedrock, STS y Groq se reemplazan por un envío falso.
"""
import base64
import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from api_client import ApiClient
from test_ia import respuesta
from test_settlement import NOW, Scenario
from web_client import fast_hashing

from yapa_sdd import bedrock, ia, partners, vision
from yapa_sdd.auth import set_admin_password
from yapa_sdd.web.api import create_api

UTEC = "434415659695"
ENV = {"YAPA_BEDROCK_CLAVE_ID": "AKIDPRUEBA", "YAPA_BEDROCK_CLAVE_SECRETA": "secreta-de-prueba",
       "YAPA_GROQ_CLAVE": "g", "YAPA_GITHUB_MODELS_CLAVE": "h"}
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64
BAG = {"productos": [{"id": "PAPA-BLANCA", "unidades": 3}], "otros": []}


class Envio:
    """Envío falso: responde según la URL y guarda lo que recibió."""

    def __init__(self, bedrock_answer=None, account=UTEC, groq_answer=None):
        self.bedrock_answer = bedrock_answer if bedrock_answer is not None else BAG
        self.account = account
        self.groq_answer = groq_answer if groq_answer is not None else {"productos": []}
        self.calls = []

    def __call__(self, url, headers, body, timeout):
        self.calls.append((url, headers, body))
        if "sts." in url:
            return {"GetCallerIdentityResponse": {"GetCallerIdentityResult": {"Account": self.account}}}
        if "bedrock-runtime" in url:
            if isinstance(self.bedrock_answer, Exception):
                raise self.bedrock_answer
            return {"output": {"message": {"role": "assistant", "content": [{"text": json.dumps(self.bedrock_answer)}]}},
                    "usage": {"inputTokens": 1200, "outputTokens": 40}}
        return respuesta(self.groq_answer)

    def urls(self, part):
        return [c for c in self.calls if part in c[0]]


def client(envio, env=ENV):
    base = ia.from_env(env)
    return ia.AIClient(base.providers, post=envio) if base else None


class BedrockProviderTests(unittest.TestCase):
    def setUp(self):
        bedrock.forget_accounts()

    # BR-A
    def test_br_a_a_photo_goes_to_bedrock_first(self):
        envio = Envio()
        answer, name = client(envio).ask_json("sistema", "lista", image=("image/jpeg", JPEG), max_tokens=400)
        self.assertEqual((answer, name), (BAG, "bedrock"))
        self.assertEqual(envio.urls("groq"), [])

    # BR-B
    def test_br_b_text_never_goes_to_bedrock(self):
        envio = Envio(groq_answer={"ok": True})
        answer, name = client(envio).ask_json("sistema", "hola")
        self.assertEqual((answer, name), ({"ok": True}, "groq"))
        self.assertEqual(envio.urls("bedrock"), [])

    # BR-C
    def test_br_c_converse_request(self):
        envio = Envio()
        client(envio).ask_json("sistema", "lista", image=("image/jpeg", JPEG), max_tokens=400)
        url, headers, body = envio.urls("bedrock-runtime")[0]
        self.assertEqual(url, "https://bedrock-runtime.us-east-2.amazonaws.com/model/"
                              "us.anthropic.claude-haiku-4-5-20251001-v1%3A0/converse")
        sent = json.loads(body)
        self.assertEqual(sent["system"], [{"text": "sistema"}])
        image = sent["messages"][0]["content"][0]["image"]
        self.assertEqual(image["format"], "jpeg")
        self.assertEqual(base64.b64decode(image["source"]["bytes"]), JPEG)
        self.assertEqual(sent["messages"][0]["content"][1], {"text": "lista"})
        self.assertEqual(sent["inferenceConfig"]["maxTokens"], 400)
        auth = headers["Authorization"]
        self.assertTrue(auth.startswith("AWS4-HMAC-SHA256 Credential=AKIDPRUEBA/"))
        self.assertIn("/us-east-2/bedrock/aws4_request", auth)

    # BR-D
    def test_br_d_signature_matches_the_aws_example(self):
        headers = bedrock.signed_headers(
            "GET", "https://iam.amazonaws.com/?Action=ListUsers&Version=2010-05-08", b"",
            key_id="AKIDEXAMPLE", secret="wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY", region="us-east-1", service="iam",
            now=datetime(2015, 8, 30, 12, 36, tzinfo=timezone.utc),
            content_type="application/x-www-form-urlencoded; charset=utf-8")
        self.assertTrue(headers["Authorization"].endswith(
            "Signature=5d672d79c15b13162d9279b0855cfba6789a8edb4c82c400e06b5924a6f2b5d7"))
        self.assertIn("SignedHeaders=content-type;host;x-amz-date", headers["Authorization"])

    # BR-E
    def test_br_e_bedrock_down_groq_answers(self):
        for error in (ia.AIError("HTTP Error 403: Forbidden"), ia.AIError("HTTP Error 429: Too Many Requests")):
            envio = Envio(bedrock_answer=error, groq_answer={"productos": [{"id": "X", "unidades": 1}]})
            _, name = client(envio).ask_json("s", "u", image=("image/jpeg", JPEG))
            self.assertEqual(name, "groq")

    # BR-F
    def test_br_f_wrong_account_turns_bedrock_off(self):
        envio = Envio(account="111111111111")
        ai = client(envio, ENV | {"YAPA_BEDROCK_CUENTA": UTEC})
        for _ in range(2):
            _, name = ai.ask_json("s", "u", image=("image/jpeg", JPEG))
            self.assertEqual(name, "groq")
        self.assertEqual(envio.urls("bedrock-runtime"), [])
        self.assertEqual(len(envio.urls("sts.")), 1)

    def test_br_f_right_account_is_checked_once(self):
        envio = Envio()
        ai = client(envio, ENV | {"YAPA_BEDROCK_CUENTA": UTEC})
        for _ in range(2):
            _, name = ai.ask_json("s", "u", image=("image/jpeg", JPEG))
            self.assertEqual(name, "bedrock")
        self.assertEqual(len(envio.urls("sts.")), 1)
        self.assertEqual(len(envio.urls("bedrock-runtime")), 2)

    # BR-G
    def test_br_g_system_aws_variables_are_not_used(self):
        ai = ia.from_env({"AWS_ACCESS_KEY_ID": "AKIAOTRA", "AWS_SECRET_ACCESS_KEY": "otra", "YAPA_GROQ_CLAVE": "g"})
        self.assertEqual([p.name for p in ai.providers], ["groq"])


class BagWithBedrockTests(unittest.TestCase):
    # BR-H
    def test_br_h_bag_review_uses_bedrock(self):
        bedrock.forget_accounts()
        fast_hashing(self)
        s = Scenario()
        order = s.order("Z-JM-01")
        set_admin_password(s.store, "admin-yapa", "yapa-admin-2026")
        partners.create_staff(s.store, "armado-78", partners.PACKER, "Rosa", "clave-prueba-2026", by="admin-yapa", now=NOW)
        envio = Envio()
        only_bedrock = {"YAPA_BEDROCK_CLAVE_ID": "AKIDPRUEBA", "YAPA_BEDROCK_CLAVE_SECRETA": "secreta"}
        app = create_api(s.store, clock=lambda: NOW, ai=client(envio, only_bedrock))
        packer = ApiClient(app)
        self.assertEqual(packer.login("armado-78", "clave-prueba-2026", partners.PACKER)[0], 200)
        with patch.object(vision, "analyze_photo") as detector:
            status, body = packer.post_file("/api/vision/analizar", {"pedido": str(order.order_id)},
                                            {"foto_archivo": ("bolsa.jpg", JPEG)})
        self.assertEqual(status, 200)
        self.assertEqual(body["fuente"], "ia")
        self.assertEqual([(p["codigo"], p["cantidad"]) for p in body["productos"]], [("PAPA-BLANCA", 3)])
        detector.assert_not_called()


if __name__ == "__main__":
    unittest.main()
