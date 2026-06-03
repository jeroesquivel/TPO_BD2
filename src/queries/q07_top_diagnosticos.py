"""Consulta 7 — Top 5 diagnósticos más frecuentes.

Motor: MongoDB. Técnica: `$group` por `diagnostico` + `$sort` desc + `$limit 5`.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def top_diagnosticos(limite: int = 5) -> list[dict]:
    """Devuelve los `limite` diagnósticos más frecuentes con su conteo."""
    db = get_db()
    pipeline = [
        {"$match": {"diagnostico": {"$ne": ""}}},
        {"$group": {"_id": "$diagnostico", "frecuencia": {"$sum": 1}}},
        {"$sort": {"frecuencia": -1, "_id": 1}},
        {"$limit": limite},
        {"$project": {"_id": 0, "diagnostico": "$_id", "frecuencia": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 7 - Top 5 diagnósticos", top_diagnosticos())
