"""Cache-aside sobre Redis para VetSalud.

"""

from __future__ import annotations

import json

from src.db.redis_client import get_redis

TTL_DEFAULT = 3600    # 1 h (consultas normales)
TTL_LARGO = 43200     # 12 h (agregados casi estáticos, ej. q07)


def cache_key(name: str, *parts) -> str:
    return "cache:" + ":".join([name, *map(str, parts)])


def get_or_set_cache(key: str, ttl: int, fetch_fn):
    r = get_redis()
    cached = r.get(key)
    if cached is not None:
        return json.loads(cached)
    res = fetch_fn()
    r.set(key, json.dumps(res, default=str), ex=ttl)
    return res


def invalidate(*names):
    """Borra todas las variantes cacheadas de cada consulta (con/sin parámetros)."""
    r = get_redis()
    for name in names:
        for k in r.scan_iter(f"cache:{name}*"):
            r.delete(k)


def flush_cache():
    r = get_redis()
    for k in r.scan_iter("cache:*"):
        r.delete(k)
