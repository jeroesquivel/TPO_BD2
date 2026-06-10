"""Consulta 1 — Pacientes activos con todos sus datos de propietario.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def pacientes_activos_con_propietario() -> list[dict]:
    """Devuelve los pacientes activos junto a los datos de su propietario."""
    db = get_db()
    pipeline = [
        {"$match": {"activo": True}},
        {"$lookup": {
            "from": "propietarios",
            "localField": "id_propietario",
            "foreignField": "id_propietario",
            "as": "propietario",
        }},
        {"$unwind": "$propietario"},
        {"$project": {
            "_id": 0,
            "id_paciente": 1,
            "nombre": 1,
            "especie": 1,
            "raza": 1,
            "propietario": {
                "nombre": "$propietario.nombre",
                "apellido": "$propietario.apellido",
                "dni": "$propietario.dni",
                "email": "$propietario.email",
                "telefono": "$propietario.telefono",
                "ciudad": "$propietario.ciudad",
                "provincia": "$propietario.provincia",
            },
        }},
        {"$sort": {"id_paciente": 1}},
    ]
    return list(db.pacientes.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 1 - Pacientes activos con propietario",
                 pacientes_activos_con_propietario())
