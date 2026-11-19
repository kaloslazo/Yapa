# Banco de fotos de bolsas · medición del 18/11/2026

Para decidir con números cómo revisar las bolsas por foto (iteración 77). Se arma y se mide con `api/tools/banco_bolsas.py`.

## El banco

- **46 fotos con respuesta conocida**: las 16 fotos del catálogo solas (12 productos que se venden y 4 que no: tomate, aceite, arroz y leche) y 30 montajes de 2 a 4 productos del catálogo sobre fondo de bolsa de papel.
- Cada foto trae un **pedido**: los productos que se ven más 3 que no están. Así, filtrar "solo lo del pedido" no basta para acertar.
- Se arma siempre igual (semilla 76), así que cualquiera lo puede repetir.
- **Límite**: no son bolsas reales. Los productos no se tapan entre sí, la luz es pareja y no hay manos ni rótulos. En una bolsa de verdad los tres métodos deberían salir peor.

## Qué se midió

| | Qué hace |
|---|---|
| A | Detector local (YOLOv8 Small de Aaron) como estaba antes de la 76: todo lo que detecta va a la pantalla. |
| B | El mismo detector como quedó en la 76: solo lo que corresponde a un producto del pedido. |
| C | IA de visión de Groq (`qwen/qwen3.8-27b`) con la lista del pedido, con el mismo mensaje y la misma limpieza que la app (`bag_reader.py`). |
| D | Lo mismo por Amazon Bedrock de la cuenta estudiantil UTEC (iteración 78): Nova 2 Lite y Nova Pro. |

- **Aciertos**: productos del pedido que están en la foto y se sugieren.
- **Inventados**: productos sugeridos que no están en la foto (en A también cuenta lo que no es del pedido).
- **Faltantes**: productos que están en la foto y no se sugieren.
- **Papa sin elegir**: el detector local dice "papa" y el pedido tiene las dos papas; el armador tiene que elegir.
- **Precisión**: de lo sugerido, cuánto es verdad. **Cobertura**: de lo que hay, cuánto se encuentra.

## Resultado

Las 46 fotos (el detector local responde siempre):

| | Aciertos | Inventados | Faltantes | Fotos perfectas | Precisión | Cobertura |
|---|---|---|---|---|---|---|
| A · YOLO como antes de la 76 | 29 | 25 | 77 | 5 de 46 | 54 % | 27 % |
| B · YOLO filtrado por pedido (76) | 29 | 7 | 77 | 9 de 46 | 81 % | 27 % |
| D · Nova 2 Lite (Bedrock) | 76 | 2 | 30 | 28 de 46 | 97 % | 72 % |
| D · **Nova Pro (Bedrock)** | **100** | **5** | **6** | **38 de 46** | **95 %** | **94 %** |

Groq (C) respondió 33 de las 46: cortó por su límite gratuito, primero por minuto (unas 7000 fichas) y después por día (200 000 fichas, unas 80 fotos). Comparación en esas mismas 33 fotos:

| | Aciertos | Inventados | Faltantes | Fotos perfectas | Precisión | Cobertura |
|---|---|---|---|---|---|---|
| B · YOLO filtrado | 22 | 6 | 44 | 9 de 33 | 79 % | 33 % |
| C · Groq | 65 | 1 | 1 | 32 de 33 | 98 % | 98 % |
| D · Nova 2 Lite | 49 | 2 | 17 | 23 de 33 | 96 % | 74 % |
| D · Nova Pro | 63 | 3 | 3 | 29 de 33 | 95 % | 95 % |

Claude Haiku 4.5 por Bedrock no se pudo medir: la cuenta UTEC todavía no envió el formulario de caso de uso de Anthropic que Bedrock pide antes de usar modelos Claude.

### Dónde falla cada uno

- **YOLO** solo conoce papa, cebolla, ajo y zanahoria: camote, limón, plátano y los galones no los puede encontrar, y a la leche, el limón y el tomate les dice cebolla. No distingue papa blanca de amarilla.
- **Groq** confundió una vez la lejía con el detergente (los dos son galones). El problema es el cupo gratuito, no la calidad.
- **Nova Pro** confunde galones (lavavajillas o lejía por detergente o limpiatodo) y a veces las dos papas; en 2 fotos le faltó un producto.
- **Nova 2 Lite** acierta lo que dice, pero deja cosas sin decir: cuando duda entre papa blanca y amarilla la pone en "otros".

## Cómo repetirlo

```bash
python3 -m venv api/.venv && api/.venv/bin/pip install pillow   # y torch + ultralytics para A y B (README del modelo)
api/.venv/bin/python api/tools/banco_bolsas.py armar public/images/products /tmp/banco
api/.venv/bin/python api/tools/banco_bolsas.py medir /tmp/banco AB
YAPA_GROQ_CLAVE=... api/.venv/bin/python api/tools/banco_bolsas.py medir /tmp/banco C   # Groq: ~25 min por el cupo gratis
# Bedrock (cuenta UTEC): credenciales del perfil utec en las variables propias de Yapa, sin Groq
eval "$(aws configure export-credentials --profile utec --format env)"
YAPA_BEDROCK_CLAVE_ID=$AWS_ACCESS_KEY_ID YAPA_BEDROCK_CLAVE_SECRETA=$AWS_SECRET_ACCESS_KEY YAPA_BEDROCK_CUENTA=434415659695 \
  YAPA_BEDROCK_MODELO=us.amazon.nova-pro-v1:0 BANCO_PAUSA=1 python3 api/tools/banco_bolsas.py medir /tmp/banco C
```
