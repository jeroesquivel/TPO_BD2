"""Conexión a Redis para el stock farmacéutico de VetSalud.
"""

from __future__ import annotations

import os
from functools import lru_cache

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


@lru_cache(maxsize=None)
def get_redis() -> redis.Redis:
    """Devuelve un cliente Redis cacheado con respuestas decodificadas a str."""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


def ping() -> bool:
    """Verifica la conexión al servidor Redis. Lanza excepción si falla."""
    return bool(get_redis().ping())


if __name__ == "__main__":  # pragma: no cover
    ping()
    print(f"Conexión Redis OK -> {REDIS_HOST}:{REDIS_PORT}")
