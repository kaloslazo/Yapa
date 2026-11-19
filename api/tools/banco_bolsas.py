"""Banco de fotos con respuesta conocida para medir la revisión de bolsas (iteración 77).

    python api/tools/banco_bolsas.py armar public/images/products /tmp/banco
    python api/tools/banco_bolsas.py medir /tmp/banco AB      # detector local (necesita api/.venv con torch)
    python api/tools/banco_bolsas.py medir /tmp/banco C       # IA (necesita YAPA_GROQ_CLAVE)

El banco: las 16 fotos del catálogo solas (12 que se venden y 4 que no) y 30 montajes de 2 a 4 productos sobre fondo
de bolsa. Cada foto trae un "pedido" con lo que se ve más 3 productos que no están, para que filtrar no alcance.
No son bolsas reales: los productos no se tapan entre sí. Necesita Pillow.

A: detector local como estaba antes de la 76 (todo a la pantalla). B: detector local como en la 76 (solo lo del
pedido). C: la IA de la 77, con el mismo mensaje y la misma limpieza que la app (`bag_reader`).
"""
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

CATALOG = {
    "PAPA-AMARILLA": ("Papa amarilla", "papa-amarilla.webp"),
    "PAPA-BLANCA": ("Papa blanca", "papa-blanca.webp"),
    "CAMOTE": ("Camote amarillo", "camote.webp"),
    "CEBOLLA-ROJA": ("Cebolla roja", "cebolla-roja.webp"),
    "AJO": ("Ajo", "ajo.webp"),
    "LIMON": ("Limón", "limon.webp"),
    "ZANAHORIA": ("Zanahoria", "zanahoria.webp"),
    "PLATANO-SEDA": ("Plátano de seda", "platano-seda.webp"),
    "LIMPIATODO-GALON": ("Limpiatodo galón 3.8 L", "limpiatodo.webp"),
    "LAVAVAJILLAS-GALON": ("Lavavajillas galón", "lavavajillas.webp"),
    "DETERGENTE-LIQUIDO-GALON": ("Detergente líquido galón", "detergente-liquido.webp"),
    "LEJIA-GALON": ("Lejía galón", "lejia.webp"),
}
NOT_SOLD = ["tomate-italiano.webp", "aceite-vegetal.webp", "arroz-extra.webp", "leche-pack.webp"]
SIZE = (900, 680)
SEED = 76
GROQ_PAUSE = int(os.environ.get("BANCO_PAUSA", "30"))  # el nivel gratuito deja ~7000 fichas por minuto y cada foto gasta ~2000


# ---------- armar ----------

def _background(rng):
    from PIL import Image, ImageFilter
    color = (196 + rng.randint(-8, 8), 160 + rng.randint(-8, 8), 118 + rng.randint(-8, 8))
    base = Image.new("RGB", SIZE, color)
    noise = Image.effect_noise(SIZE, 22).convert("RGB")
    return Image.blend(base, noise, 0.08).filter(ImageFilter.GaussianBlur(0.6))


def _cells(n):
    w, h = SIZE
    if n == 1:
        return [(80, 60, w - 80, h - 60)]
    if n == 2:
        return [(20, 60, w // 2, h - 60), (w // 2, 60, w - 20, h - 60)]
    return [(20, 20, w // 2, h // 2), (w // 2, 20, w - 20, h // 2), (20, h // 2, w // 2, h - 20),
            (w // 2, h // 2, w - 20, h - 20)][:n]


def _place(canvas, item, box, rng):
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / item.width, (y1 - y0) / item.height) * rng.uniform(0.75, 0.95)
    resized = item.resize((max(1, int(item.width * scale)), max(1, int(item.height * scale))))
    resized = resized.rotate(rng.uniform(-12, 12), expand=True)
    canvas.paste(resized, (x0 + (x1 - x0 - resized.width) // 2, y0 + (y1 - y0 - resized.height) // 2), resized)


def build(src: str, out: str) -> None:
    from PIL import Image
    rng = random.Random(SEED)
    folder = Path(out)
    folder.mkdir(parents=True, exist_ok=True)
    files = [f for _, f in CATALOG.values()] + NOT_SOLD
    images = {name: Image.open(Path(src) / name).convert("RGBA") for name in files}
    cases = []

    def save(name, items, truth):
        canvas = _background(rng)
        for item, box in zip(items, _cells(len(items))):
            _place(canvas, images[item], box, rng)
        canvas.save(folder / f"{name}.jpg", quality=86)
        others = [c for c in CATALOG if c not in truth]
        cases.append({"foto": f"{name}.jpg", "verdad": sorted(truth), "pedido": sorted(truth + rng.sample(others, 3))})

    for code, (_, file) in CATALOG.items():
        save(f"suelta-{code.lower()}", [file], [code])
    for file in NOT_SOLD:
        save(f"suelta-{file.split('.')[0]}", [file], [])
    for i in range(30):
        truth = rng.sample(list(CATALOG), rng.choice([2, 3, 4]))
        save(f"bolsa-{i + 1:02d}", [CATALOG[c][1] for c in truth], truth)
    names = {code: name for code, (name, _) in CATALOG.items()}
    (folder / "banco.json").write_text(json.dumps({"nombres": names, "casos": cases}, ensure_ascii=False, indent=1))
    print(f"{len(cases)} fotos en {folder}")


# ---------- medir ----------

def _detector_rows(found, order, names, keep_unknown):
    """Lo que vería el armador con el detector local: código, "?" (papa sin elegir) o "x" (algo fuera del pedido)."""
    from yapa_sdd.bag_reader import _kind
    rows = []
    for p in found:
        matches = [c for c in order if _kind(names[c]) == p["producto"]]
        if not matches and not keep_unknown:
            continue
        rows.append(matches[0] if len(matches) == 1 else ("?" if matches else "x"))
    return rows


def _ai_rows(ai, order, names, photo):
    from yapa_sdd import bag_reader
    products = {c: names[c] for c in order}
    for _ in range(4):
        result = bag_reader._with_ai(ai, products, photo)
        if result is not None:
            return [p["codigo"] for p in result["productos"]], result["otros"]
        time.sleep(30)  # cupo del minuto agotado: se espera y se reintenta
    return None, []


def _score(rows, truth):
    picked = {r for r in rows if r not in ("?", "x")}
    return len(picked & set(truth)), len(picked - set(truth)) + rows.count("x"), len(set(truth) - picked), rows.count("?")


def measure(bank: str, methods: str) -> None:
    from yapa_sdd import ia, vision
    data = json.loads((Path(bank) / "banco.json").read_text())
    names, cases = data["nombres"], data["casos"]
    only = [f for f in os.environ.get("BANCO_SOLO", "").split(",") if f]  # repetir solo algunas fotos
    cases = [c for c in cases if not only or c["foto"] in only]
    ai = ia.from_env(os.environ) if "C" in methods else None
    totals = {m: {"aciertos": 0, "inventados": 0, "faltantes": 0, "papa_sin_elegir": 0, "perfectas": 0, "sin_respuesta": 0}
              for m in methods}
    detail = []
    for case in cases:
        photo = (Path(bank) / case["foto"]).read_bytes()
        line = {"foto": case["foto"], "verdad": case["verdad"]}
        found = None
        for m in methods:
            if m in "AB":
                found = found if found is not None else vision.analyze_photo(("f.jpg", photo))["productos"]
                rows = _detector_rows(found, case["pedido"], names, keep_unknown=(m == "A"))
            else:
                rows, others = _ai_rows(ai, case["pedido"], names, photo)
                time.sleep(GROQ_PAUSE)
                if rows is None:
                    totals[m]["sin_respuesta"] += 1
                    rows = []
                line["C_otros"] = others
            tp, fp, fn, unsure = _score(rows, case["verdad"])
            for key, value in zip(("aciertos", "inventados", "faltantes", "papa_sin_elegir"), (tp, fp, fn, unsure)):
                totals[m][key] += value
            totals[m]["perfectas"] += int(fp == fn == unsure == 0)
            line[m] = rows
        detail.append(line)
        print(json.dumps(line, ensure_ascii=False), flush=True)
    print("\nmétodo | aciertos | inventados | faltantes | papa sin elegir | fotos perfectas | precisión | cobertura")
    for m, t in totals.items():
        tp, fp, fn = t["aciertos"], t["inventados"], t["faltantes"]
        precision = tp / (tp + fp) if tp + fp else 0
        coverage = tp / (tp + fn) if tp + fn else 0
        print(f"{m} | {tp} | {fp} | {fn} | {t['papa_sin_elegir']} | {t['perfectas']}/{len(cases)} | {precision:.0%} | {coverage:.0%}"
              + (f" | sin respuesta: {t['sin_respuesta']}" if t["sin_respuesta"] else ""))
    suffix = "-parcial" if only else ""
    (Path(bank) / f"resultado-{methods}{suffix}.json").write_text(
        json.dumps({"totales": totals, "detalle": detail}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if len(sys.argv) < 4 and not (len(sys.argv) == 3 and sys.argv[1] == "medir"):
        sys.exit(__doc__)
    if sys.argv[1] == "armar":
        build(sys.argv[2], sys.argv[3])
    else:
        measure(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "ABC")
