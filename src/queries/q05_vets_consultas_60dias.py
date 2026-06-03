"""Consulta 5 — Veterinarios activos y cantidad de consultas realizadas en los
últimos 60 días.

Motor: MongoDB. Técnica: `match` por fecha `>= hoy-60d` + `$group` por `id_vet`
+ `$lookup` a veterinarios filtrando los activos. El límite de fecha se calcula
en código con `datetime` (no se hardcodea) para que sea reproducible.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from src.db.mongo import get_db
from src.queries._util import print_result


def vets_activos_consultas_ultimos_60_dias(referencia: datetime | None = None) -> list[dict]:
    """Cuenta las consultas de los últimos 60 días por veterinario activo.

    Args:
        referencia: fecha de corte (por defecto `datetime.now()`).
    """
    db = get_db()
    ahora = referencia or datetime.now()
    desde = ahora - timedelta(days=60)
    pipeline = [
        {"$match": {"fecha": {"$gte": desde, "$lte": ahora}}},
        {"$group": {"_id": "$id_vet", "consultas_60d": {"$sum": 1}}},
        {"$lookup": {
            "from": "veterinarios",
            "localField": "_id",
            "foreignField": "id_vet",
            "as": "vet",
        }},
        {"$unwind": "$vet"},
        {"$match": {"vet.activo": True}},
        {"$project": {
            "_id": 0,
            "id_vet": "$_id",
            "veterinario": {"$concat": ["$vet.nombre", " ", "$vet.apellido"]},
            "sucursal": "$vet.sucursal",
            "consultas_60d": 1,
        }},
        {"$sort": {"consultas_60d": -1, "id_vet": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 5 - Vets activos y consultas (últimos 60 días)",
                 vets_activos_consultas_ultimos_60_dias())
