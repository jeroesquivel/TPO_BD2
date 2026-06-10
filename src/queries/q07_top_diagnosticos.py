"""Consulta 7 — Top 5 diagnósticos más frecuentes.

"""

from __future__ import annotations

from src.db.mongo import get_db


def top_diagnosticos(limite: int = 5) -> list[dict]:
    """Devuelve los `limite` diagnósticos más frecuentes con su conteo."""
    db = get_db()
    pipeline = [
        {"$match": {"diagnostico": {"$nin": ["", None]}}},
        {"$group": {"_id": "$diagnostico", "frecuencia": {"$sum": 1}}},
        {"$sort": {"frecuencia": -1, "_id": 1}},
        {"$limit": limite},
        {"$project": {"_id": 0, "diagnostico": "$_id", "frecuencia": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))
