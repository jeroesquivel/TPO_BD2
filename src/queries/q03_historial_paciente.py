"""Consulta 3 — Historial completo de un paciente: consultas y vacunaciones
ordenadas por fecha (enunciado §4 #3).
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result

# Eventos de consulta (raíz del pipeline) y de vacunación (unión), normalizados a
# una línea de tiempo común. Las cirugías quedan aparte (ver historial_completo).
_PROJ_CONSULTA = {
    "_id": 0,
    "tipo": {"$literal": "Consulta"},
    "fecha": "$fecha",
    "detalle": "$motivo",
    "diagnostico": "$diagnostico",
    "id_vet": "$id_vet",
}

_UNION_VACUNACIONES = {
    "coll": "vacunaciones",
    "pipeline": [
        {"$project": {
            "_id": 0,
            "tipo": {"$literal": "Vacunación"},
            "fecha": "$fecha_aplicacion",
            "detalle": "$nombre_vacuna",
            "diagnostico": {"$literal": None},
            "id_vet": "$id_vet",
        }},
    ],
}

_UNION_CIRUGIAS = {
    "coll": "cirugias",
    "pipeline": [
        {"$project": {
            "_id": 0,
            "tipo": {"$literal": "Cirugía"},
            "fecha": "$fecha",
            "detalle": "$tipo",
            "diagnostico": "$resultado",
            "id_vet": "$id_vet",
        }},
    ],
}


def _historial(id_paciente: str, incluir_cirugias: bool) -> list[dict]:
    db = get_db()
    union_vac = {**_UNION_VACUNACIONES}
    union_vac["pipeline"] = [{"$match": {"id_paciente": id_paciente}}, *union_vac["pipeline"]]
    pipeline = [
        {"$match": {"id_paciente": id_paciente}},
        {"$project": _PROJ_CONSULTA},
        {"$unionWith": union_vac},
    ]
    if incluir_cirugias:
        union_cir = {**_UNION_CIRUGIAS}
        union_cir["pipeline"] = [{"$match": {"id_paciente": id_paciente}}, *union_cir["pipeline"]]
        pipeline.append({"$unionWith": union_cir})
    pipeline.append({"$sort": {"fecha": 1}})
    return list(db.consultas.aggregate(pipeline))


def historial_paciente(id_paciente: str) -> list[dict]:
    """Línea de tiempo del paciente: consultas + vacunaciones (enunciado §4 #3)."""
    return _historial(id_paciente, incluir_cirugias=False)


def historial_completo(id_paciente: str) -> list[dict]:
    """Variante extendida: historial + cirugías (extra, fuera del enunciado §4 #3)."""
    return _historial(id_paciente, incluir_cirugias=True)


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 3 - Historial del paciente P001",
                 historial_paciente("P001"))
    print_result("Consulta 3 (extendida) - Historial completo de P001",
                 historial_completo("P001"))
