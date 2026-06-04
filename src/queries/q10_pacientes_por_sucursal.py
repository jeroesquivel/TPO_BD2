"""Consulta 10 — Todos los pacientes de una sucursal determinada (a través del
veterinario que los atendió).

Motor: MongoDB. Técnica: `$lookup` encadenado veterinarios (por sucursal) →
consultas → pacientes, con `$group` para deduplicar pacientes atendidos en la
sucursal.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def pacientes_por_sucursal(sucursal: str) -> list[dict]:
    """Devuelve los pacientes atendidos por veterinarios de una sucursal dada."""
    db = get_db()
    pipeline = [
        {"$match": {"sucursal": sucursal}},
        # vet -> consultas que realizó
        {"$lookup": {
            "from": "consultas",
            "localField": "id_vet",
            "foreignField": "id_vet",
            "as": "consultas",
        }},
        {"$unwind": "$consultas"},
        # consulta -> paciente
        {"$lookup": {
            "from": "pacientes",
            "localField": "consultas.id_paciente",
            "foreignField": "id_paciente",
            "as": "paciente",
        }},
        {"$unwind": "$paciente"},
        # deduplicar por paciente
        {"$group": {
            "_id": "$paciente.id_paciente",
            "nombre": {"$first": "$paciente.nombre"},
            "especie": {"$first": "$paciente.especie"},
            "veterinarios": {"$addToSet": {
                "$concat": ["$nombre", " ", "$apellido"]}},
        }},
        {"$project": {
            "_id": 0,
            "id_paciente": "$_id",
            "nombre": 1,
            "especie": 1,
            "veterinarios": 1,
        }},
        {"$sort": {"id_paciente": 1}},
    ]
    return list(db.veterinarios.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 10 - Pacientes de la sucursal Palermo",
                 pacientes_por_sucursal("Palermo"))
