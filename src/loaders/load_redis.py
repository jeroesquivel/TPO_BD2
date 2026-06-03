"""ETL CSV -> Redis para el stock farmacéutico de VetSalud.

Modelo de datos (sección 6):
- `stock:<id_producto>`  -> hash con los campos del producto.
- `productos`           -> set con todos los `id_producto` (para iterar sin `KEYS`).
- `vencimientos`        -> sorted set con score = timestamp del vencimiento.

Limpieza aplicada: `strip()` de textos, normalización de la categoría con punto
final sobrante, `unidades`/`precio_unit` a numérico, y `vencimiento` guardado
como string legible en el hash y como timestamp en el sorted set.
"""

from __future__ import annotations

import csv
from pathlib import Path

from src.db.redis_client import get_redis
from src.loaders.clean import (
    clean_str,
    normalize_categoria,
    parse_date,
    parse_number,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STOCK_PREFIX = "stock:"
SET_PRODUCTOS = "productos"
ZSET_VENCIMIENTOS = "vencimientos"


def _read_csv(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _clear(r) -> None:
    """Elimina del datastore todas las claves del stock (carga idempotente)."""
    ids = r.smembers(SET_PRODUCTOS)
    keys = [f"{STOCK_PREFIX}{pid}" for pid in ids]
    if keys:
        r.delete(*keys)
    r.delete(SET_PRODUCTOS, ZSET_VENCIMIENTOS)


def upsert_producto(r, row: dict) -> str:
    """Inserta/actualiza un producto en sus tres estructuras y devuelve su id."""
    pid = clean_str(row["id_producto"])
    vencimiento = parse_date(row["vencimiento"])
    hash_doc = {
        "nombre": clean_str(row["nombre"]),
        "categoria": normalize_categoria(row["categoria"]),
        "unidades": parse_number(row["unidades"]),
        "precio_unit": parse_number(row["precio_unit"]),
        "vencimiento": vencimiento.strftime("%Y-%m-%d") if vencimiento else "",
        "proveedor": clean_str(row["proveedor"]),
    }
    pipe = r.pipeline()
    pipe.hset(f"{STOCK_PREFIX}{pid}", mapping=hash_doc)
    pipe.sadd(SET_PRODUCTOS, pid)
    if vencimiento:
        pipe.zadd(ZSET_VENCIMIENTOS, {pid: vencimiento.timestamp()})
    pipe.execute()
    return pid


def load(clear: bool = True) -> int:
    """Ejecuta el ETL del stock hacia Redis.

    Args:
        clear: si es True, limpia el stock anterior antes de cargar.

    Returns:
        Cantidad de productos cargados.
    """
    r = get_redis()
    if clear:
        _clear(r)

    rows = _read_csv("stock_farmaceutico.csv")
    for row in rows:
        upsert_producto(r, row)
    return len(rows)


if __name__ == "__main__":  # pragma: no cover
    n = load()
    print(f"ETL Redis completado: {n} productos en stock")
