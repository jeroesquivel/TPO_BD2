"""Consulta 6 — Pacientes con vacunas vencidas (próxima dosis anterior a hoy).

Motor: MongoDB. Técnica: `find(proxima_dosis < datetime.now())` + `$lookup` a
`pacientes`. El corte temporal se calcula dinámicamente.
"""

from __future__ import annotations

from datetime import datetime

from src.db.mongo import get_db
from src.queries._util import print_result


def vacunas_vencidas(referencia: datetime | None = None) -> list[dict]:
    """Devuelve las vacunaciones cuya próxima dosis ya venció, con el paciente."""
    db = get_db()
    ahora = referencia or datetime.now()
    pipeline = [
        {"$match": {"proxima_dosis": {"$lt": ahora}}},
        {"$lookup": {
            "from": "pacientes",
            "localField": "id_paciente",
            "foreignField": "id_paciente",
            "as": "paciente",
        }},
        {"$unwind": "$paciente"},
        {"$project": {
            "_id": 0,
            "id_vacuna": 1,
            "id_paciente": 1,
            "paciente": "$paciente.nombre",
            "especie": "$paciente.especie",
            "nombre_vacuna": 1,
            "fecha_aplicacion": 1,
            "proxima_dosis": 1,
        }},
        {"$sort": {"proxima_dosis": 1}},
    ]
    return list(db.vacunaciones.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 6 - Pacientes con vacunas vencidas",
                 vacunas_vencidas())
