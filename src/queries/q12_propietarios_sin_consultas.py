"""Consulta 12 — Propietarios sin consultas registradas en el último año.

Motor: MongoDB. Técnica: **un solo** `$lookup` correlacionado de `propietarios`
a `consultas` por `id_propietario` (campo desnormalizado), con filtro de fecha.
Elimina la cadena doble propietarios → pacientes → consultas.

Supuesto: `id_propietario` en cada consulta es un snapshot del dueño al momento
de la atención. Un cambio de dueño posterior no afecta el historial registrado.
El caso borde "propietario con 0 pacientes" se incluye correctamente (sin
consultas → aparece en el resultado).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.db.mongo import get_db
from src.queries._util import print_result


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
            "propietario": {"$concat": ["$nombre", " ", "$apellido"]},
            "email": 1,
            "ciudad": 1,
        }},
        {"$sort": {"id_propietario": 1}},
    ]
    return list(db.propietarios.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 12 - Propietarios sin consultas en el último año",
                 propietarios_sin_consultas_ultimo_anio())
