"""Hace la semana de la demo paso a paso contra el motor de demo_semana.py: python api/tools/semana_demo.py <paso>

Pasos, en orden: miercoles, jueves, viernes, sabado, domingo, siguiente (o "todo" para la semana entera).
Cada paso mueve el reloj, hace lo que haría cada rol ese día y dice qué mirar en la web.
El motor se elige con YAPA_API (por omisión http://127.0.0.1:8010). Solo usa la biblioteca estándar.
"""

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from yapa_sdd.web.__main__ import DEMO_ADMIN, DEMO_DRIVER, DEMO_PINS, DEMO_STAFF, DEMO_SUPPLIER  # noqa: E402

API = os.environ.get("YAPA_API", "http://127.0.0.1:8010").rstrip("/")
PASOS = ("miercoles", "jueves", "viernes", "sabado", "domingo", "siguiente")
CANASTA_ANA = {"PAPA-AMARILLA": "8", "CEBOLLA-ROJA": "6", "LEJIA-GALON": "3"}  # con su lejía el grupo pasa los 12 galones
CANASTA_SIGUIENTE = {"PAPA-AMARILLA": "8", "CEBOLLA-ROJA": "6", "AJO": "1", "LIMON": "3"}
STAFF = {kind: (user, password) for user, password, kind, _, _ in DEMO_STAFF}
FOTO = Path(__file__).resolve().parents[2] / "public" / "images" / "products" / "papa-amarilla.webp"  # foto de prueba


class Falla(Exception):
    pass


class Cuenta:
    """Una sesión por rol, con su cookie y su token CSRF."""

    def __init__(self, tipo: str, usuario: str, secreto: str):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf = ""
        self.csrf = self.pedir("POST", "/api/sesion", {"tipo": tipo, "usuario": usuario, "secreto": secreto})["csrf"]

    def pedir(self, metodo: str, ruta: str, datos=None, foto: bool = False):
        cabeceras = {"X-Yapa-CSRF": self.csrf} if self.csrf else {}
        cuerpo = None
        if foto:
            limite = uuid.uuid4().hex
            partes = [f'--{limite}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                      for k, v in (datos or {}).items()]
            partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="foto_archivo"; filename="{FOTO.name}"\r\n'
                          f"Content-Type: image/webp\r\n\r\n".encode() + FOTO.read_bytes() + b"\r\n")
            partes.append(f"--{limite}--\r\n".encode())
            cuerpo = b"".join(partes)
            cabeceras["Content-Type"] = f"multipart/form-data; boundary={limite}"
        elif datos is not None:
            cuerpo = json.dumps(datos).encode()
            cabeceras["Content-Type"] = "application/json"
        try:
            with self.opener.open(urllib.request.Request(API + ruta, data=cuerpo, method=metodo, headers=cabeceras)) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as error:
            try:
                mensaje = json.loads(error.read())["error"]["mensaje"]
            except (ValueError, KeyError):
                mensaje = f"respuesta {error.code}"
            raise Falla(f"{metodo} {ruta}: {mensaje}") from None


def entrar(rol: str) -> Cuenta:
    if rol == "admin":
        return Cuenta("admin", *DEMO_ADMIN)
    if rol == "ana":
        return Cuenta("vecino", "101", DEMO_PINS[101])
    if rol == "transportista":
        return Cuenta("transportista", *DEMO_DRIVER)
    if rol == "proveedor":
        return Cuenta("proveedor", *DEMO_SUPPLIER)
    return Cuenta(rol, *STAFF[rol])


def mover_reloj(paso: str) -> dict:
    urllib.request.urlopen(f"{API}/api/demo/reloj?ir={paso}").read()
    estado = json.loads(urllib.request.urlopen(f"{API}/api/estado").read())
    print(f"\n== {paso.upper()} · {estado['ahora'][:16].replace('T', ' ')} · ciclo {estado['ciclo']} "
          f"{'abierto' if estado['abierto'] else 'cerrado'}")
    return estado


def pedido_de_ana(ana: Cuenta, ciclo: str):
    return next((p for p in ana.pedir("GET", "/api/mis-pedidos")["pedidos"] if p["ciclo"] == ciclo), None)


def miercoles():
    ciclo = mover_reloj("miercoles")["ciclo"]
    ana = entrar("ana")
    pedido = pedido_de_ana(ana, ciclo) or ana.pedir("POST", "/api/pedidos", {"lineas": CANASTA_ANA, "metodo": "YAPE"})
    print(f"Ana (vecina y admin de Los Álamos) pidió: pedido {pedido['id']}, yapea S/ {pedido['a_yapear']} "
          f"con el código {pedido['codigo_pago']}")
    admin = entrar("admin")
    pendientes = admin.pedir("GET", "/api/admin/resumen")["por_verificar"]
    for orden in pendientes:
        admin.pedir("POST", f"/api/admin/pedidos/{orden['id']}/verificar")
    avance = ana.pedir("GET", "/api/mi-zona").get("avance") or {}
    print(f"El admin verificó {len(pendientes)} pagos. Grupo de Los Álamos: {avance.get('verificados')} de {avance.get('minimo')} pedidos")
    print("Mira: Ana > Inicio (el grupo llegó a 8) y Mis pedidos (pago verificado); admin > Resumen.")


def jueves():
    ciclo = mover_reloj("jueves")["ciclo"]
    compras = entrar("compras")
    compras.pedir("POST", "/api/compras/recibido", {"ciclo": ciclo, "recibido": {}})
    compras.pedir("POST", "/api/compras/flete", {"ciclo": ciclo, "empresa": "Fletes Santa Anita", "monto": "120"})
    print("Compras registró que llegó todo del mayorista y el flete de S/ 120.")
    print("Mira: compras > Compra de la semana; proveedor > lo que Yapa le compra; Ana > Mis pedidos (Comprado).")


def viernes():
    ciclo = mover_reloj("viernes")["ciclo"]
    armado = entrar("armador")
    por_armar = [p for p in armado.pedir("GET", f"/api/admin/armado?ciclo={ciclo}")["pedidos"] if not p["bolsas"]]
    for orden in por_armar:
        armado.pedir("POST", "/api/admin/bolsas", {"pedido": orden["id"]}, foto=True)
    print(f"Armado registró {len(por_armar)} bolsas, cada una con su foto y su rótulo.")
    print("Mira: armado > Armado y entrega; Ana > Mis pedidos (Armado, con la foto de su bolsa).")


def sabado():
    ciclo = mover_reloj("sabado")["ciclo"]
    reparto = entrar("transportista")
    for parada in reparto.pedir("GET", f"/api/reparto?ciclo={ciclo}")["paradas"]:
        if parada["estado"] != "pendiente":
            continue
        zona = parada["zona"]
        reparto.pedir("POST", "/api/reparto/salidas", {"ciclo": ciclo, "zona": zona["id"]})
        reparto.pedir("POST", "/api/reparto/entregas", {"ciclo": ciclo, "zona": zona["id"], "recibe": zona["contacto"]}, foto=True)
        print(f"Reparto salió hacia {zona['nombre']} y dejó {len(parada['pedidos'])} pedidos con foto ({zona['contacto']}).")
    entrar("porteria").pedir("POST", "/api/porteria/recepciones", {"ciclo": ciclo})
    print("La portería de Los Álamos confirmó que recibió las bolsas; cada vecino recibe el aviso.")
    print("Mira: reparto > su hoja; portería > recepción; Ana > Mis pedidos (En camino y Entregado) y la campana.")


def domingo():
    ciclo = mover_reloj("domingo")["ciclo"]
    ana, admin = entrar("ana"), entrar("admin")
    pedido = pedido_de_ana(ana, ciclo)
    reclamo = ana.pedir("POST", "/api/reclamos", {"pedido": pedido["id"], "producto": "CEBOLLA-ROJA", "cantidad": "1",
                                                   "motivo": "DANADO"}, foto=True)
    print(f"Ana reclamó 1 kg de cebolla dañada con foto (reclamo {reclamo['id']}).")
    liquidacion = admin.pedir("POST", f"/api/admin/ciclos/{ciclo}/liquidar")
    nombres = {p["id"]: p["nombre"].lower() for p in ana.pedir("GET", "/api/catalogo")["productos"]}
    bajaron = [p for p in liquidacion["productos"] if p["tramo"] != "0"]
    print("El admin liquidó la semana: " + ", ".join(f"{nombres.get(p['id'], p['id'])} bajó a S/ {p['precio_final']}"
                                                   for p in bajaron)
          + f"; vuelven S/ {liquidacion['a_saldo']} al saldo de los vecinos.")
    entrar("atencion").pedir("POST", f"/api/admin/reclamos/{reclamo['id']}/revisar", {"decision": "aprobar"})
    mio = next(o for o in liquidacion["pedidos"] if o["id"] == pedido["id"])
    saldo = ana.pedir("GET", "/api/mis-pedidos")["saldo"]
    cuadra = admin.pedir("GET", "/api/admin/conciliacion")["diferencia"]
    print(f"Atención aprobó el reclamo. Ana pagó S/ {mio['pagado']}, costó S/ {mio['costo']}, le devolvemos "
          f"S/ {mio['devuelto']} y su saldo queda en S/ {saldo}. Conciliación: diferencia S/ {cuadra}.")
    print("Mira: Ana > Mis pedidos (Te devolvemos, reclamo aprobado); atención > Reclamos; admin > Conciliación y Métricas.")


def siguiente():
    ciclo = mover_reloj("siguiente")["ciclo"]
    ana = entrar("ana")
    pedido = pedido_de_ana(ana, ciclo) or ana.pedir("POST", "/api/pedidos", {"lineas": CANASTA_SIGUIENTE, "metodo": "YAPE",
                                                                             "usar_saldo": True})
    print(f"Semana nueva: Ana pidió S/ {pedido['total']}, usó S/ {pedido['con_saldo']} de su saldo y yapea "
          f"S/ {pedido['a_yapear']}.")
    print("Mira: Ana > Mis pedidos (el saldo ya se usó).")


def main() -> None:
    paso = sys.argv[1] if len(sys.argv) > 1 else ""
    if paso not in (*PASOS, "todo"):
        sys.exit(f"Uso: semana_demo.py <{'|'.join(PASOS)}|todo>")
    try:
        for nombre in PASOS if paso == "todo" else (paso,):
            globals()[nombre]()
    except Falla as error:
        sys.exit(f"No se pudo: {error}\n(Los pasos van en orden: {', '.join(PASOS)}. Para empezar de cero, reinicia el motor.)")
    except urllib.error.URLError:
        sys.exit(f"No hay motor en {API}. Levántalo con scripts/demo.sh")


if __name__ == "__main__":
    main()
