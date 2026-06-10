"""Consulta 2 — Consultas médicas abiertas (estado 'Seguimiento') con
veterinario asignado y costo.

Motor: MongoDB. Técnica: `match` por estado + `$project` que arma el objeto del
veterinario desde el snapshot desnormalizado de `consultas` (0 lookups).
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def consultas_en_seguimiento() -> list[dict]:
    """Devuelve las consultas en estado 'Seguimiento' con su veterinario y costo."""
    db = get_db()
    pipeline = [
        {"$match": {"estado": "Seguimiento"}},
        {"$project": {
            "_id": 0,
            "id_consulta": 1,
            "id_paciente": 1,
            "fecha": 1,
            "motivo": 1,
            "diagnostico": 1,
            "costo": 1,
            "veterinario": {
                "id_vet": "$id_vet",
                "nombre": "$vet_nombre",
                "apellido": "$vet_apellido",
                "especialidad": "$vet_especialidad",
                "sucursal": "$vet_sucursal",
            },
        }},
        {"$sort": {"fecha": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 2 - Consultas en Seguimiento",
                 consultas_en_seguimiento())
