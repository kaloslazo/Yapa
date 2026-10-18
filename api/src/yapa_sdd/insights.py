"""Iteración 37: análisis por zona y propuestas del sistema (docs/desarrollo/37-analisis-zonas-propuestas.md).

Solo lee: no mueve dinero ni zonas (AN-07). Las propuestas son sugerencias para el admin de Yapa (S-189).
"""

from __future__ import annotations

from decimal import Decimal

from . import cycle, metrics, zones
from .domain import MIN_ORDERS_PER_GROUP
from .store import InMemoryStore

ZERO = Decimal("0")
PROPOSAL_ORDER = ["UNIR", "RECORDAR", "INVITAR", "REVISAR_COSTO", "REACTIVAR"]  # AN-05


def _active_orders(store: InMemoryStore, cycle_id: str) -> list:
    return [o for o in store.orders_in_cycle(cycle_id) if o.status != "CANCELADO"]


def _groups(store: InMemoryStore) -> dict[str, list]:
    groups: dict[str, list] = {}
    for zone in sorted(store.zones.values(), key=lambda z: z.zone_id):
        groups.setdefault(zone.group_id, []).append(zone)
    return groups


def _zone_rows(store: InMemoryStore, cycle_id: str) -> list[dict]:
    margins = metrics.order_margins(store, cycle_id) if cycle_id in store.settlements else None
    orders = _active_orders(store, cycle_id)
    rows = []
    for zone in sorted(store.zones.values(), key=lambda z: z.zone_id):
        neighbors = [c for c in store.customers.values() if c.zone_id == zone.zone_id]
        placed = [o for o in orders if o.zone_id == zone.zone_id]
        margin = None
        if margins is not None:
            margin = sum((margins[o.order_id].margin for o in placed if o.order_id in margins), ZERO)
        rows.append({"id": zone.zone_id, "nombre": zone.name, "distrito": zone.district, "grupo": zone.group_id,
                     "estado": zone.status, "lat": zone.lat, "lon": zone.lon, "vecinos": len(neighbors),
                     "pedidos": len(placed),
                     "verificados": sum(1 for o in placed if o.payment_status == "VERIFICADO"),
                     "adopcion": round(len(placed) * 100 / len(neighbors)) if neighbors else 0,  # S-182
                     "margen": margin})
    return rows


def _unions(store: InMemoryStore, now) -> list[dict]:
    """AN-03: pares de zonas de grupos distintos a MERGE_DISTANCE_M o menos."""
    located = sorted((z for z in store.zones.values() if z.lat is not None and z.lon is not None), key=lambda z: z.zone_id)
    found = []
    for i, a in enumerate(located):
        for b in located[i + 1:]:
            meters = zones.distance_m(a.lat, a.lon, b.lat, b.lon)
            if a.group_id != b.group_id and meters <= zones.MERGE_DISTANCE_M:
                found.append({"a": a.zone_id, "b": b.zone_id, "distancia_m": round(meters),
                              "motivo": zones.merge_blocker(store, a, b, now) or ""})
    return found


def _propose_merges(store: InMemoryStore, unions: list[dict], by_group: dict[str, dict]) -> list[dict]:
    """S-183: una propuesta por par de grupos, con el par de zonas más cercano que se puede unir hoy."""
    closest: dict[tuple[str, str], dict] = {}
    for union in unions:
        if union["motivo"]:
            continue
        key = tuple(sorted((store.zones[union["a"]].group_id, store.zones[union["b"]].group_id)))
        if key not in closest or union["distancia_m"] < closest[key]["distancia_m"]:
            closest[key] = union
    proposals = []
    for (group_a, group_b), union in sorted(closest.items()):
        verified_a, verified_b = by_group[group_a]["verificados"], by_group[group_b]["verificados"]
        together = verified_a + verified_b
        both_reach = verified_a >= MIN_ORDERS_PER_GROUP and verified_b >= MIN_ORDERS_PER_GROUP
        if both_reach or together < MIN_ORDERS_PER_GROUP:
            continue
        a, b = store.zones[union["a"]], store.zones[union["b"]]
        proposals.append({"tipo": "UNIR", "zonas": [a.zone_id, b.zone_id], "titulo": f"Unir {a.name} y {b.name}",
                          "detalle": (f"Están a {union['distancia_m']} m. Juntas suman {together} pedidos verificados y el "
                                      f"mínimo es {MIN_ORDERS_PER_GROUP}. Los dos admins deben estar de acuerdo."),
                          "datos": {"distancia_m": union["distancia_m"], "verificados_juntos": together,
                                    "minimo": MIN_ORDERS_PER_GROUP}})
    return proposals


def _group_summary(store: InMemoryStore, cycle_id: str) -> dict[str, dict]:
    orders = _active_orders(store, cycle_id)
    summary = {}
    for group_id, members in _groups(store).items():
        ids = {z.zone_id for z in members}
        neighbors = [c for c in store.customers.values() if c.zone_id in ids]
        placed = {o.customer_id for o in orders if o.zone_id in ids}
        summary[group_id] = {
            "zonas": [z for z in members if any(c.zone_id == z.zone_id for c in store.customers.values())],
            "activa": any(z.status == "ACTIVA" for z in members),
            "vecinos": len(neighbors),
            "sin_pedir": len([c for c in neighbors if c.customer_id not in placed]),
            "verificados": sum(1 for o in orders if o.zone_id in ids and o.payment_status == "VERIFICADO"),
        }
    return summary


def _names(group_zones: list) -> str:
    return " + ".join(z.name for z in group_zones)


def _propose_for_groups(by_group: dict[str, dict]) -> list[dict]:
    proposals = []
    for group_id, g in sorted(by_group.items()):
        if not g["zonas"] or not g["activa"] or g["verificados"] >= MIN_ORDERS_PER_GROUP:
            continue
        ids, names = [z.zone_id for z in g["zonas"]], _names(g["zonas"])
        if g["vecinos"] < MIN_ORDERS_PER_GROUP:  # S-185
            proposals.append({"tipo": "INVITAR", "zonas": ids, "titulo": f"Invitar más vecinos en {names}",
                              "detalle": (f"Tiene {g['vecinos']} vecinos y el mínimo es {MIN_ORDERS_PER_GROUP}: aunque todos pidan, "
                                          "no llega. Su admin puede invitar con el premio por referido."),
                              "datos": {"vecinos": g["vecinos"], "minimo": MIN_ORDERS_PER_GROUP}})
        elif g["sin_pedir"] and g["verificados"] + g["sin_pedir"] >= MIN_ORDERS_PER_GROUP:  # S-184
            proposals.append({"tipo": "RECORDAR", "zonas": ids, "titulo": f"Recordar a los vecinos de {names}",
                              "detalle": (f"Faltan {g['sin_pedir']} vecinos por pedir. Si piden y pagan, llegan a "
                                          f"{g['verificados'] + g['sin_pedir']} de {MIN_ORDERS_PER_GROUP}."),
                              "datos": {"sin_pedir": g["sin_pedir"], "verificados": g["verificados"]}})
    return proposals


def _propose_money(store: InMemoryStore, cycle_id: str, rows: list[dict]) -> list[dict]:
    proposals = []
    for row in rows:  # S-186
        if row["margen"] is not None and row["margen"] < 0:
            proposals.append({"tipo": "REVISAR_COSTO", "zonas": [row["id"]], "titulo": f"Revisar el costo de {row['nombre']}",
                              "detalle": f"La semana {cycle_id} esta zona dejó un margen de S/ {row['margen']:.2f}. Revisa la parada y los reclamos.",
                              "datos": {"margen": f"{row['margen']:.2f}", "pedidos": row["pedidos"]}})
    previous = cycle.add_weeks(cycle_id, -1)
    received = {o.customer_id for o in store.orders_in_cycle(previous) if o.status == "LIQUIDADO"}
    ordering = {o.customer_id for o in _active_orders(store, cycle_id)}
    for zone in sorted(store.zones.values(), key=lambda z: z.zone_id):  # S-187
        silent = [c for c in store.customers.values() if c.zone_id == zone.zone_id
                  and c.customer_id in received and c.customer_id not in ordering]
        if silent:
            proposals.append({"tipo": "REACTIVAR", "zonas": [zone.zone_id], "titulo": f"Reactivar a vecinos de {zone.name}",
                              "detalle": f"{len(silent)} vecinos recibieron su pedido la semana {previous} y aún no piden esta semana.",
                              "datos": {"vecinos": len(silent), "semana_anterior": previous}})
    return proposals


def analysis(store: InMemoryStore, cycle_id: str, now) -> dict:
    """AN-01: zonas, uniones posibles y propuestas de la semana `cycle_id`."""
    rows = _zone_rows(store, cycle_id)
    unions = _unions(store, now)
    by_group = _group_summary(store, cycle_id)
    proposals = (_propose_merges(store, unions, by_group) + _propose_for_groups(by_group)
                 + _propose_money(store, cycle_id, rows))
    proposals.sort(key=lambda p: (PROPOSAL_ORDER.index(p["tipo"]), p["zonas"]))  # AN-05
    return {"ciclo": cycle_id, "zonas": rows, "uniones": unions, "propuestas": proposals}
