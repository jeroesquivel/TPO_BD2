"""Consulta 12 — Propietarios sin consultas registradas en el último año.

Motor: MongoDB. Técnica: `$lookup` propietarios → pacientes → consultas (con
`match` por fecha `>= hoy-365d`) y se filtran los propietarios cuyo resultado de
consultas recientes queda vacío. El corte de un año se calcula dinámicamente.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.db.mongo import get_db
from src.queries._util import print_result


def propietarios_sin_consultas_ultimo_anio(referencia: datetime | None = None) -> list[dict]:
    """Devuelve los propietarios sin consultas en los últimos 365 días."""
    db = get_db()
    corte = (referencia or datetime.now()) - timedelta(days=365)
    pipeline = [
        {"$lookup": {
            "from": "pacientes",
            "localField": "id_propietario",
            "foreignField": "id_propietario",
            "as": "pacientes",
        }},
        # Por cada propietario, traer las consultas recientes de cualquiera de
        # sus pacientes.
        {"$lookup": {
            "from": "consultas",
            "let": {"ids": "$pacientes.id_paciente"},
            "pipeline": [
                {"$match": {"$expr": {"$and": [
                    {"$in": ["$id_paciente", "$$ids"]},
                    {"$gte": ["$fecha", corte]},
                ]}}},
            ],
            "as": "consultas_recientes",
        }},
        {"$match": {"consultas_recientes": {"$size": 0}}},
        {"$project": {
            "_id": 0,
            "id_propietario": 1,
            "propietario": {"$concat": ["$nombre", " ", "$apellido"]},
            "email": 1,
            "ciudad": 1,
            "cantidad_pacientes": {"$size": "$pacientes"},
        }},
        {"$sort": {"id_propietario": 1}},
    ]
    return list(db.propietarios.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 12 - Propietarios sin consultas en el último año",
                 propietarios_sin_consultas_ultimo_anio())
