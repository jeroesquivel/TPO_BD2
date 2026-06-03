"""Consulta 2 — Consultas médicas abiertas (estado 'Seguimiento') con
veterinario asignado y costo.

Motor: MongoDB. Técnica: `match` por estado + `$lookup` a `veterinarios`.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def consultas_en_seguimiento() -> list[dict]:
    """Devuelve las consultas en estado 'Seguimiento' con su veterinario y costo."""
    db = get_db()
    pipeline = [
        {"$match": {"estado": "Seguimiento"}},
        {"$lookup": {
            "from": "veterinarios",
            "localField": "id_vet",
            "foreignField": "id_vet",
            "as": "veterinario",
        }},
        {"$unwind": "$veterinario"},
        {"$project": {
            "_id": 0,
            "id_consulta": 1,
            "id_paciente": 1,
            "fecha": 1,
            "motivo": 1,
            "diagnostico": 1,
            "costo": 1,
            "estado": 1,
            "veterinario": {
                "$concat": ["$veterinario.nombre", " ", "$veterinario.apellido"],
            },
            "especialidad": "$veterinario.especialidad",
        }},
        {"$sort": {"fecha": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 2 - Consultas en Seguimiento",
                 consultas_en_seguimiento())
