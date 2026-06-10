"""Conexión a MongoDB para VetSalud.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "vetsalud")


@lru_cache(maxsize=None)
def get_client() -> MongoClient:
    """Devuelve un `MongoClient` cacheado apuntando a `MONGO_URI`."""
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def get_db(name: str | None = None) -> Database:
    """Devuelve la base de datos `vetsalud` (o la indicada en `name`)."""
    return get_client()[name or MONGO_DB]


def ping() -> bool:
    """Verifica la conexión al servidor MongoDB. Lanza excepción si falla."""
    get_client().admin.command("ping")
    return True


if __name__ == "__main__":  # pragma: no cover
    ping()
    print(f"Conexión MongoDB OK -> {MONGO_URI} (db: {MONGO_DB})")
