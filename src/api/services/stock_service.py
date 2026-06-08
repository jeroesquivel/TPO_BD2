from src.db.cache import get_or_set_cache, invalidate, cache_key, TTL_DEFAULT
from src.queries import (
    q08_stock_bajo        as q08,
    q15_decrementar_stock as q15,
)


def get_stock_bajo(umbral: int = 50):
    return get_or_set_cache(cache_key("q08", umbral), TTL_DEFAULT,
                            lambda: q08.stock_bajo(umbral))


def decrementar_stock(id_producto: str, cantidad: int):
    out = q15.decrementar_stock(id_producto, cantidad)
    invalidate("q08")
    return out
