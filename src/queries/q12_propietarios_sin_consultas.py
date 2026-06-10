"""Consulta 12 — Propietarios sin consultas registradas en el último año.

"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.db.mongo import get_db


def propietarios_sin_consultas_ultimo_anio(referencia: datetime | None = None) -> list[dict]:
    """Devuelve los propietarios sin consultas en los últimos 365 días.

    La ventana es [corte, ahora]: una consulta con fecha futura no cuenta como
    reciente (cota superior simétrica a la consulta 5).
    """
    db = get_db()
    ahora = referencia or datetime.now()
    corte = ahora - timedelta(days=365)
    pipeline = [
        {"$lookup": {
            "from": "consultas",
            "let": {"pid": "$id_propietario"},
            "pipeline": [{"$match": {"$expr": {"$and": [
                {"$eq":  ["$id_propietario", "$$pid"]},
                {"$gte": ["$fecha", corte]},
                {"$lte": ["$fecha", ahora]},
            ]}}}],
            "as": "consultas_recientes",
        }},
        {"$match": {"consultas_recientes": {"$size": 0}}},
        {"$project": {
            "_id": 0,
            "id_propietario": 1,
            "nombre": 1,
            "apellido": 1,
            "dni": 1,
            "email": 1,
            "telefono": 1,
            "ciudad": 1,
            "provincia": 1,
        }},
        {"$sort": {"id_propietario": 1}},
    ]
    return list(db.propietarios.aggregate(pipeline))
