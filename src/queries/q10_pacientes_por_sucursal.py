"""Consulta 10 — Todos los pacientes de una sucursal determinada (a través del
veterinario que los atendió).

Motor: MongoDB. Técnica: `$match` por `vet_sucursal` (campo desnormalizado) +
`$group` para deduplicar + **un solo** `$lookup` a `pacientes`. Elimina la
cadena doble veterinarios → consultas → pacientes.

Supuesto: pertenencia a sucursal = haber tenido al menos una consulta atendida
por un veterinario de esa sucursal (no vacunación/cirugía).
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def pacientes_por_sucursal(sucursal: str) -> list[dict]:
    """Devuelve los pacientes atendidos por veterinarios de una sucursal dada."""
    db = get_db()
    pipeline = [
        {"$match": {"vet_sucursal": sucursal}},
        {"$group": {
            "_id": "$id_paciente",
            "veterinarios": {"$addToSet": {
                "$concat": ["$vet_nombre", " ", "$vet_apellido"]}},
        }},
        {"$lookup": {
            "from": "pacientes",
            "localField": "_id",
            "foreignField": "id_paciente",
            "as": "paciente",
        }},
        {"$unwind": "$paciente"},
        {"$project": {
            "_id": 0,
            "id_paciente": "$_id",
            "nombre": "$paciente.nombre",
            "especie": "$paciente.especie",
            "veterinarios": 1,
        }},
        {"$sort": {"id_paciente": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 10 - Pacientes de la sucursal Palermo",
                 pacientes_por_sucursal("Palermo"))
