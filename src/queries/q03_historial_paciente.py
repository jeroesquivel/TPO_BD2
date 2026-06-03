"""Consulta 3 — Historial completo de un paciente: consultas y vacunaciones
ordenadas por fecha.

Motor: MongoDB. Técnica: `$unionWith` de ambas colecciones + `$sort` por fecha.
Se unifican consultas y vacunaciones en una única línea de tiempo, normalizando
el campo de fecha (`fecha` para consultas, `fecha_aplicacion` para vacunas).
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def historial_paciente(id_paciente: str) -> list[dict]:
    """Devuelve la línea de tiempo (consultas + vacunaciones) de un paciente."""
    db = get_db()
    pipeline = [
        {"$match": {"id_paciente": id_paciente}},
        {"$project": {
            "_id": 0,
            "tipo": {"$literal": "Consulta"},
            "fecha": "$fecha",
            "detalle": "$motivo",
            "diagnostico": "$diagnostico",
            "id_vet": "$id_vet",
        }},
        {"$unionWith": {
            "coll": "vacunaciones",
            "pipeline": [
                {"$match": {"id_paciente": id_paciente}},
                {"$project": {
                    "_id": 0,
                    "tipo": {"$literal": "Vacunación"},
                    "fecha": "$fecha_aplicacion",
                    "detalle": "$nombre_vacuna",
                    "diagnostico": {"$literal": None},
                    "id_vet": "$id_vet",
                }},
            ],
        }},
        {"$sort": {"fecha": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 3 - Historial del paciente P001",
                 historial_paciente("P001"))
