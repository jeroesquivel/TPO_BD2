"""Consulta 8 — Stock de productos con menos de 50 unidades y su proveedor.
"""

from __future__ import annotations

from src.db.mongo import get_db


def stock_bajo(umbral: int = 50) -> list[dict]:
    """Devuelve los productos con `unidades < umbral`, con proveedor y precio."""
    db = get_db()
    cursor = db.stock.find(
        {"unidades": {"$lt": umbral}},
        {"_id": 0, "id_producto": 1, "nombre": 1, "categoria": 1,
         "unidades": 1, "precio_unit": 1, "proveedor": 1},
    ).sort("unidades", 1)
    return list(cursor)
