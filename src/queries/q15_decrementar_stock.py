"""Consulta 15 — Actualización masiva del stock: decrementar unidades de un
producto tras una consulta.

Motor: **Redis**. Técnica: `HINCRBY stock:<id> unidades -<n>` (operación atómica,
sin condiciones de carrera). Se valida que el producto exista y que el stock no
quede negativo; para el control de stock insuficiente se usa una transacción con
`WATCH` (patrón check-and-set) que aborta si otra escritura modifica el hash.
"""

from __future__ import annotations

import redis

from src.db.redis_client import get_redis
from src.loaders.load_redis import SET_PRODUCTOS, STOCK_PREFIX
from src.queries._util import print_result


class StockError(ValueError):
    """Error de stock: producto inexistente o unidades insuficientes."""


def decrementar_stock(id_producto: str, cantidad: int) -> dict:
    """Decrementa `cantidad` unidades de un producto de forma atómica y segura.

    Args:
        id_producto: identificador del producto (p. ej. "PRD001").
        cantidad: unidades a descontar (entero positivo).

    Returns:
        Dict con el estado antes/después del decremento.

    Raises:
        StockError: si el producto no existe, la cantidad es inválida o no hay
            stock suficiente.
    """
    if cantidad <= 0:
        raise StockError("La cantidad a decrementar debe ser positiva")

    r = get_redis()
    key = f"{STOCK_PREFIX}{id_producto}"

    if not r.sismember(SET_PRODUCTOS, id_producto) or not r.exists(key):
        raise StockError(f"El producto {id_producto} no existe")

    # Transacción optimista: WATCH bloquea si otro cliente toca la clave entre
    # la lectura y el HINCRBY, evitando dejar el stock negativo.
    with r.pipeline() as pipe:
        while True:
            try:
                pipe.watch(key)
                actual = int(pipe.hget(key, "unidades") or 0)
                if actual < cantidad:
                    pipe.unwatch()
                    raise StockError(
                        f"Stock insuficiente de {id_producto}: "
                        f"hay {actual}, se pidieron {cantidad}")
                pipe.multi()
                pipe.hincrby(key, "unidades", -cantidad)
                nuevo = pipe.execute()[0]
                break
            except redis.WatchError:  # pragma: no cover - reintento por contención
                continue

    return {
        "id_producto": id_producto,
        "unidades_antes": actual,
        "decremento": cantidad,
        "unidades_despues": nuevo,
    }


if __name__ == "__main__":  # pragma: no cover
    resultado = decrementar_stock("PRD001", 5)
    print_result("Consulta 15 - Decremento de stock", [resultado])
    try:
        decrementar_stock("PRD006", 10_000)
    except StockError as exc:
        print(f"\nValidación OK -> {exc}")
