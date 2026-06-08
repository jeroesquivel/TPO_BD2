"""Consulta 11 — Vista agregada: ingresos totales por veterinario en el mes actual.

Motor: MongoDB. Técnica: `match` por el rango del mes actual + `$group` por
`id_vet` con `$sum: "$costo"`. Usa los campos desnormalizados
`vet_nombre`/`vet_apellido`/`vet_sucursal` como `$first` en el grupo (0 lookups).

Supuesto: ingresos = suma de todas las consultas del mes, independientemente
del estado (incluye "Seguimiento").
"""

from __future__ import annotations

from datetime import datetime

from src.db.mongo import get_db
from src.queries._util import print_result


def _rango_mes_actual(referencia: datetime) -> tuple[datetime, datetime]:
    inicio = referencia.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)
    return inicio, fin


def ingresos_por_vet_mes_actual(referencia: datetime | None = None) -> list[dict]:
    """Devuelve los ingresos totales por veterinario en el mes en curso."""
    db = get_db()
    inicio, fin = _rango_mes_actual(referencia or datetime.now())
    pipeline = [
        {"$match": {"fecha": {"$gte": inicio, "$lt": fin}}},
        {"$group": {
            "_id": "$id_vet",
            "vet_nombre":   {"$first": "$vet_nombre"},
            "vet_apellido": {"$first": "$vet_apellido"},
            "vet_sucursal": {"$first": "$vet_sucursal"},
            "ingresos":           {"$sum": "$costo"},
            "cantidad_consultas": {"$sum": 1},
        }},
        {"$project": {
            "_id": 0,
            "id_vet":    "$_id",
            "veterinario": {"$concat": ["$vet_nombre", " ", "$vet_apellido"]},
            "sucursal":  "$vet_sucursal",
            "ingresos": 1,
            "cantidad_consultas": 1,
        }},
        {"$sort": {"ingresos": -1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 11 - Ingresos por veterinario (mes actual)",
                 ingresos_por_vet_mes_actual())
