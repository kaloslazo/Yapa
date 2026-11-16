"""Arma una base poblada (la semana actual con 6 semanas de historia) conservando las cuentas de una base existente.

Uso: python api/tools/poblar_base.py <base-actual.db> <base-nueva.db> <carpeta-fotos>
Las cuentas, claves y PIN salen de la base actual: no crea contraseñas de demo. Se usó el 16/11/2026 para producción
(respaldo de la base anterior en /opt/yapa/backups/antes-de-poblar-20261116.db); ver deploy/aws/README.md.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import demo_semana  # noqa: E402
from yapa_sdd import persistence  # noqa: E402
from yapa_sdd.cycle import LIMA  # noqa: E402


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    actual, nueva, fotos = sys.argv[1:]
    viejo = persistence.load(actual)
    store = demo_semana.armar(datetime.now(LIMA), credenciales=False, completa=False)
    store.partners, store.credentials = viejo.partners, viejo.credentials
    store.admins |= viejo.admins
    store.debug_admins |= viejo.debug_admins
    demo_semana.poblar(store, True)
    demo_semana.fotos_de_la_semilla(store, carpeta=fotos)
    persistence.save(store, nueva)
    print(f"{nueva}: {len(store.orders)} pedidos, {len(store.customers)} vecinos, {len(store.settlements)} semanas liquidadas")


if __name__ == "__main__":
    main()
