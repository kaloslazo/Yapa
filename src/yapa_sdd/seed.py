"""Catálogo, zonas y clientes del piloto (S-12: precios de ejemplo).

Los precios base salen de los mayoristas reales del 23-24/09/2026
(docs/analisis/08_validacion_economica.md); el limpiatodo es el precio
real de Kaz en distribuidora. Se reemplazan por la lista del proveedor aliado.
"""

from __future__ import annotations

from decimal import Decimal as D

from .domain import Customer, PriceTier, Product, Zone
from .store import InMemoryStore


def _tiers(*pairs):
    return tuple(PriceTier(D(qty), D(price)) for qty, price in pairs)


PILOT_PRODUCTS = [
    Product("PAPA-AMARILLA", "Papa amarilla", "FRESCOS", "kg", D("1"), D("400"),
            _tiers(("0", "3.60"), ("100", "3.38"), ("250", "3.20"))),
    Product("PAPA-BLANCA", "Papa blanca", "FRESCOS", "kg", D("1"), D("600"),
            _tiers(("0", "1.10"), ("100", "0.98"), ("250", "0.90"))),
    Product("CEBOLLA-ROJA", "Cebolla roja", "FRESCOS", "kg", D("1"), D("300"),
            _tiers(("0", "2.10"), ("80", "1.80"), ("200", "1.45"))),
    Product("AJO", "Ajo criollo", "FRESCOS", "kg", D("0.25"), D("40"),
            _tiers(("0", "4.80"), ("20", "4.40"))),
    Product("LIMON", "Limón", "FRESCOS", "kg", D("1"), D("150"),
            _tiers(("0", "2.10"), ("50", "1.90"))),
    Product("CAMOTE", "Camote amarillo", "FRESCOS", "kg", D("1"), D("200"),
            _tiers(("0", "1.20"), ("80", "1.05"))),
    Product("ZANAHORIA", "Zanahoria", "FRESCOS", "kg", D("1"), D("200"),
            _tiers(("0", "1.60"), ("80", "1.44"))),
    # Descartado por margen en el límite (08_validacion_economica.md).
    Product("PLATANO-SEDA", "Plátano de seda", "FRESCOS", "kg", D("1"), D("100"),
            _tiers(("0", "2.63"),), active=False),
    Product("LIMPIATODO-GALON", "Limpiatodo galón 3.8 L", "LIMPIEZA", "unidad", D("1"), D("60"),
            _tiers(("0", "7.90"), ("12", "6.90"))),
    Product("LAVAVAJILLAS-GALON", "Lavavajillas galón", "LIMPIEZA", "unidad", D("1"), D("60"),
            _tiers(("0", "9.50"), ("12", "8.60"))),
    Product("DETERGENTE-LIQUIDO-GALON", "Detergente líquido galón", "LIMPIEZA", "unidad", D("1"), D("60"),
            _tiers(("0", "14.00"), ("12", "12.50"))),
    Product("LEJIA-GALON", "Lejía galón", "LIMPIEZA", "unidad", D("1"), D("60"),
            _tiers(("0", "6.50"), ("12", "5.80"))),
]

PILOT_ZONES = [
    Zone("Z-LINCE-01", "Edificio Los Álamos", "Lince", "G-LINCE", D("40")),
    Zone("Z-LINCE-02", "Condominio Las Palmeras", "Lince", "G-LINCE", D("40")),
    Zone("Z-JM-01", "Residencial San Felipe", "Jesús María", "G-JM", D("40")),
    Zone("Z-LV-01", "Edificio Balconcillo", "La Victoria", "G-LV", D("40"), reception_accepted=False),
    Zone("Z-MIRA-01", "Edificio Larco", "Miraflores", "G-MIRA", D("40")),
]

PILOT_CUSTOMERS = [
    Customer(101, "Ana Torres", "Z-LINCE-01"),
    Customer(102, "Luis Ramos", "Z-LINCE-01", suspended=True),
    Customer(103, "Rosa Quispe", "Z-LV-01"),
    Customer(104, "Jorge Salas", "Z-MIRA-01"),
    Customer(105, "Carmen Díaz", "Z-LINCE-01"),
]


def pilot_store() -> InMemoryStore:
    store = InMemoryStore()
    for product in PILOT_PRODUCTS:
        store.add_product(product)
    for zone in PILOT_ZONES:
        store.add_zone(zone)
    for customer in PILOT_CUSTOMERS:
        store.add_customer(customer)
    return store
