"""Punto de entrada de VetSalud — carga de datos.

Uso:
    python -m src.main
"""

from src.db import mongo, redis_client
from src.db.cache import flush_cache
from src.loaders import load_mongo, seed_extra


def run_etl() -> None:
    print(">> Verificando conexiones...")
    mongo.ping()
    redis_client.ping()
    print(">> Cargando MongoDB...")
    load_mongo.load()
    print(">> Cargando registros adicionales (seed)...")
    seed_extra.seed()
    print(">> Limpiando caché Redis...")
    flush_cache()
    print(">> ETL completo.")


if __name__ == "__main__":  # pragma: no cover
    run_etl()
