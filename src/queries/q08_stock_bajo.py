"""Consulta 8 — Stock de productos con menos de 50 unidades y su proveedor.

Motor: **MongoDB**. Filtra `{unidades: {$lt: umbral}}` y devuelve los campos
relevantes ordenados por unidades ascendente.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def stock_bajo(umbral: int = 50) -> list[dict]:
    """Devuelve los productos con `unidades < umbral`, con proveedor y precio."""
    db = get_db()
    cursor = db.stock.find(
        {"unidades": {"$lt": umbral}},
        {"_id": 0, "id_producto": 1, "nombre": 1, "categoria": 1,
         "unidades": 1, "precio_unit": 1, "proveedor": 1},
    ).sort("unidades", 1)
    return list(cursor)


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 8 - Stock con menos de 50 unidades", stock_bajo())
