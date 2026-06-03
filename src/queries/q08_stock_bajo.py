"""Consulta 8 — Stock de productos con menos de 50 unidades y su proveedor.

Motor: **Redis**. Técnica: iterar el set `productos`, `HGETALL` por producto y
filtrar `unidades < 50`. No se usa `KEYS` (se recorre el índice de existencia).
"""

from __future__ import annotations

from src.db.redis_client import get_redis
from src.loaders.load_redis import SET_PRODUCTOS, STOCK_PREFIX
from src.queries._util import print_result


def stock_bajo(umbral: int = 50) -> list[dict]:
    """Devuelve los productos con `unidades < umbral`, con proveedor y precio."""
    r = get_redis()
    resultado = []
    for pid in r.smembers(SET_PRODUCTOS):
        doc = r.hgetall(f"{STOCK_PREFIX}{pid}")
        if not doc:
            continue
        unidades = int(doc.get("unidades", 0))
        if unidades < umbral:
            resultado.append({
                "id_producto": pid,
                "nombre": doc.get("nombre"),
                "categoria": doc.get("categoria"),
                "unidades": unidades,
                "precio_unit": float(doc.get("precio_unit", 0)),
                "proveedor": doc.get("proveedor"),
            })
    resultado.sort(key=lambda d: d["unidades"])
    return resultado


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 8 - Stock con menos de 50 unidades", stock_bajo())
