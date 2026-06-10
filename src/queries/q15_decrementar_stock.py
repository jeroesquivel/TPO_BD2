"""Consulta 15 — Actualización masiva del stock: decrementar unidades de un
producto tras una consulta.

"""

from __future__ import annotations

from pymongo import ReturnDocument

from src.db.mongo import get_db
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

    db = get_db()
    antes = db.stock.find_one({"id_producto": id_producto}, {"_id": 0, "unidades": 1})
    if not antes:
        raise StockError(f"El producto {id_producto} no existe")

    doc = db.stock.find_one_and_update(
        {"id_producto": id_producto, "unidades": {"$gte": cantidad}},
        {"$inc": {"unidades": -cantidad}},
        return_document=ReturnDocument.AFTER,
        projection={"_id": 0, "unidades": 1},
    )
    if doc is None:
        raise StockError(
            f"Stock insuficiente de {id_producto}: hay {antes['unidades']}, "
            f"se pidieron {cantidad}")

    return {
        "id_producto": id_producto,
        "unidades_antes": antes["unidades"],
        "decremento": cantidad,
        "unidades_despues": doc["unidades"],
    }


if __name__ == "__main__":  # pragma: no cover
    resultado = decrementar_stock("PRD001", 5)
    print_result("Consulta 15 - Decremento de stock", [resultado])
    try:
        decrementar_stock("PRD006", 10_000)
    except StockError as exc:
        print(f"\nValidación OK -> {exc}")
