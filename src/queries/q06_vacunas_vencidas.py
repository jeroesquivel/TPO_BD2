"""Consulta 6 — Pacientes con vacunas vencidas (próxima dosis anterior a hoy).

"""

from __future__ import annotations

from datetime import datetime

from src.db.mongo import get_db
from src.queries._util import print_result


def vacunas_vencidas(referencia: datetime | None = None) -> list[dict]:
    """Devuelve los pacientes con vacunas vencidas; cada uno con el array de sus
    vacunaciones vencidas (con todos los datos de cada una)."""
    db = get_db()
    ahora = referencia or datetime.now()
    pipeline = [
        {"$match": {"proxima_dosis": {"$lt": ahora}}},
        {"$project": {"_id": 0}},
        {"$sort": {"proxima_dosis": 1}},  # ordena las vacunas dentro de cada array
        {"$group": {
            "_id": "$id_paciente",
            "vacunas_vencidas": {"$push": "$$ROOT"},
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
            "paciente": "$paciente.nombre",
            "especie": "$paciente.especie",
            "vacunas_vencidas": 1,
        }},
        {"$sort": {"id_paciente": 1}},
    ]
    return list(db.vacunaciones.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 6 - Pacientes con vacunas vencidas",
                 vacunas_vencidas())
