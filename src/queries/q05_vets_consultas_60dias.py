"""Consulta 5 — Veterinarios activos y cantidad de consultas realizadas en los
últimos 60 días.


"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.db.mongo import get_db


def vets_activos_consultas_ultimos_60_dias(referencia: datetime | None = None) -> list[dict]:
    """Cuenta las consultas de los últimos 60 días por veterinario activo.

    Incluye veterinarios con 0 consultas en el período.

    Args:
        referencia: fecha de corte (por defecto `datetime.now()`).
    """
    db = get_db()
    ahora = referencia or datetime.now()
    desde = ahora - timedelta(days=60)
    pipeline = [
        {"$match": {"activo": True}},
        {"$lookup": {
            "from": "consultas",
            "let": {"vid": "$id_vet"},
            "pipeline": [{"$match": {"$expr": {"$and": [
                {"$eq":  ["$id_vet", "$$vid"]},
                {"$gte": ["$fecha",  desde]},
                {"$lte": ["$fecha",  ahora]},
            ]}}}],
            "as": "consultas_recientes",
        }},
        {"$project": {
            "_id": 0,
            "id_vet": 1,
            "nombre": 1,
            "apellido": 1,
            "especialidad": 1,
            "sucursal": 1,
            "consultas_60d": {"$size": "$consultas_recientes"},
        }},
        {"$sort": {"consultas_60d": -1, "id_vet": 1}},
    ]
    return list(db.veterinarios.aggregate(pipeline))
