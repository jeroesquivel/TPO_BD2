"""Cache sobre Redis para VetSalud.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime

from redis.exceptions import RedisError

from src.db.redis_client import get_redis

log = logging.getLogger(__name__)

TTL_DEFAULT = 3600    # 1 h (consultas normales)
TTL_LARGO = 43200     # 12 h (agregados casi estáticos, ej. q07)


def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()        # fechas SIEMPRE en ISO ("2026-06-08T00:00:00")
    return str(o)


def cache_key(name: str, *parts) -> str:
    return "cache:" + ":".join([name, *map(str, parts)])


def get_or_set_cache(key: str, ttl: int, fetch_fn):
    try:
        r = get_redis()
        cached = r.get(key)
        if cached is not None:
            return json.loads(cached)
    except RedisError as exc:                      # Redis caído -> seguir contra Mongo
        log.warning("Redis no disponible (lectura %s): %s", key, exc)
        return fetch_fn()

    res = fetch_fn()
    payload = json.dumps(res, default=_json_default)   # serializar UNA vez
    try:
        r.set(key, payload, ex=ttl)
    except RedisError as exc:
        log.warning("Redis no disponible (escritura %s): %s", key, exc)
    return json.loads(payload)                      # miss devuelve igual que un hit


def invalidate(*names):
    """Borra todas las variantes cacheadas de cada consulta (con/sin parámetros).

    Best-effort: si Redis no responde, loguea y sigue para no tumbar una escritura
    que ya se persistió en Mongo.
    """
    try:
        r = get_redis()
        for name in names:
            for k in r.scan_iter(f"cache:{name}*"):
                r.delete(k)
    except RedisError as exc:
        log.warning("Redis no disponible (invalidate %s): %s", names, exc)


def flush_cache():
    try:
        r = get_redis()
        for k in r.scan_iter("cache:*"):
            r.delete(k)
    except RedisError as exc:
        log.warning("Redis no disponible (flush): %s", exc)
