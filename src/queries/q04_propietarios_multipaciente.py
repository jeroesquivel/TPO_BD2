"""Consulta 4 — Propietarios con más de un paciente registrado.

Motor: MongoDB. Técnica: `$group` por `id_propietario` con `$sum`, filtrar `> 1`
y `$lookup` para traer los datos del propietario.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def propietarios_con_varios_pacientes() -> list[dict]:
    """Devuelve los propietarios que tienen más de un paciente."""
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$id_propietario",
            "cantidad_pacientes": {"$sum": 1},
            "pacientes": {"$push": "$nombre"},
        }},
        {"$match": {"cantidad_pacientes": {"$gt": 1}}},
        {"$lookup": {
            "from": "propietarios",
            "localField": "_id",
            "foreignField": "id_propietario",
            "as": "propietario",
        }},
        {"$unwind": "$propietario"},
        {"$project": {
            "_id": 0,
            "id_propietario": "$_id",
            "propietario": {
                "$concat": ["$propietario.nombre", " ", "$propietario.apellido"],
            },
            "cantidad_pacientes": 1,
            "pacientes": 1,
        }},
        {"$sort": {"cantidad_pacientes": -1, "id_propietario": 1}},
    ]
    return list(db.pacientes.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 4 - Propietarios con más de un paciente",
                 propietarios_con_varios_pacientes())
