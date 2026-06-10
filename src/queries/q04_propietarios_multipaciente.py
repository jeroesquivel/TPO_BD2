"""Consulta 4 — Propietarios con más de un paciente registrado.


"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def propietarios_con_varios_pacientes() -> list[dict]:
    """Devuelve los propietarios que tienen más de un paciente."""
    db = get_db()
    pipeline = [
        {"$group": {
            "_id": "$id_propietario",
            "cantidad_pacientes": {"$sum": 1},
            "pacientes": {"$push": {
                "id_paciente": "$id_paciente",
                "nombre": "$nombre",
                "especie": "$especie",
                "raza": "$raza",
                "fecha_nac": "$fecha_nac",
                "activo": "$activo",
            }},
        }},
        {"$match": {"cantidad_pacientes": {"$gt": 1}}},
        {"$lookup": {
            "from": "propietarios",
            "localField": "_id",
            "foreignField": "id_propietario",
            "as": "propietario",
        }},
        {"$unwind": "$propietario"},
        {"$project": {
            "_id": 0,
            # Datos del propietario (entidad principal): planos y completos, igual
            # que q01 (anidado) y q12 (plano) — los 8 campos, sin concatenar.
            "id_propietario": "$_id",
            "nombre":    "$propietario.nombre",
            "apellido":  "$propietario.apellido",
            "dni":       "$propietario.dni",
            "email":     "$propietario.email",
            "telefono":  "$propietario.telefono",
            "ciudad":    "$propietario.ciudad",
            "provincia": "$propietario.provincia",
            "cantidad_pacientes": 1,
            "pacientes": 1,
        }},
        {"$sort": {"cantidad_pacientes": -1, "id_propietario": 1}},
    ]
    return list(db.pacientes.aggregate(pipeline))


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 4 - Propietarios con más de un paciente",
                 propietarios_con_varios_pacientes())
