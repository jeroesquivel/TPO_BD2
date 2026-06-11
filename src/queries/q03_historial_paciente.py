"""Consulta 3 — Historial completo de un paciente: consultas y vacunaciones ordenadas por fecha.
"""

from __future__ import annotations

from src.db.mongo import get_db


_PROJ_CONSULTA = {
    "_id": 0,
    "tipo": {"$literal": "Consulta"},
    "fecha": "$fecha",
    "detalle": "$motivo",
    "diagnostico": "$diagnostico",
    "id_vet": "$id_vet",
}

_PROJ_VACUNACION = {
    "_id": 0,
    "tipo": {"$literal": "Vacunación"},
    "fecha": "$fecha_aplicacion",
    "detalle": "$nombre_vacuna",
    "diagnostico": {"$literal": None},
    "id_vet": "$id_vet",
}

_PROJ_CIRUGIA = {
    "_id": 0,
    "tipo": {"$literal": "Cirugía"},
    "fecha": "$fecha",
    "detalle": "$tipo",
    "diagnostico": "$resultado",
    "id_vet": "$id_vet",
}


def _union(coll: str, id_paciente: str, proyeccion: dict) -> dict:
    """Arma un `$unionWith` que filtra la colección por paciente y la normaliza."""
    return {"coll": coll, "pipeline": [
        {"$match": {"id_paciente": id_paciente}},
        {"$project": proyeccion},
    ]}


def _historial(id_paciente: str, incluir_cirugias: bool) -> list[dict]:
    db = get_db()
    pipeline = [
        {"$match": {"id_paciente": id_paciente}},
        {"$project": _PROJ_CONSULTA},
        {"$unionWith": _union("vacunaciones", id_paciente, _PROJ_VACUNACION)},
    ]
    if incluir_cirugias:
        pipeline.append({"$unionWith": _union("cirugias", id_paciente, _PROJ_CIRUGIA)})
    pipeline.append({"$sort": {"fecha": 1}})
    return list(db.consultas.aggregate(pipeline))


def historial_paciente(id_paciente: str) -> list[dict]:
    """Línea de tiempo del paciente: consultas + vacunaciones."""
    return _historial(id_paciente, incluir_cirugias=False)


def historial_completo(id_paciente: str) -> list[dict]:
    """Variante extendida: historial + cirugías."""
    return _historial(id_paciente, incluir_cirugias=True)
