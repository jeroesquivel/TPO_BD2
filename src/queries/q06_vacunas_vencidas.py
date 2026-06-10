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
        {"$sort": {"proxima_dosis": 1}},  # ordena las vacunas dentro de cada array
        {"$group": {
            "_id": "$id_paciente",
            "vacunas_vencidas": {"$push": {
                "id_vacuna": "$id_vacuna",
                "nombre_vacuna": "$nombre_vacuna",
                "fecha_aplicacion": "$fecha_aplicacion",
                "proxima_dosis": "$proxima_dosis",
            }},
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
            "id_paciente": "$paciente.id_paciente",
            "nombre": "$paciente.nombre",
            "especie": "$paciente.especie",
            "raza": "$paciente.raza",
            "fecha_nac": "$paciente.fecha_nac",
            "id_propietario": "$paciente.id_propietario",
            "activo": "$paciente.activo",
            "vacunas_vencidas": 1,
        }},
        {"$sort": {"id_paciente": 1}},
    ]
    return list(db.vacunaciones.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 6 - Pacientes con vacunas vencidas",
                 vacunas_vencidas())
