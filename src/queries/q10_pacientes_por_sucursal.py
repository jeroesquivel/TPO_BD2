"""Consulta 10 — Todos los pacientes de una sucursal determinada (a través del
veterinario que los atendió).
"""

from __future__ import annotations

from src.db.mongo import get_db


def pacientes_por_sucursal(sucursal: str) -> list[dict]:
    """Devuelve los pacientes atendidos por veterinarios de una sucursal dada."""
    db = get_db()
    pipeline = [
        {"$match": {"vet_sucursal": sucursal}},
        {"$group": {
            "_id": "$id_paciente",
            "veterinarios": {"$addToSet": {
                "id_vet": "$id_vet",
                "nombre": "$vet_nombre",
                "apellido": "$vet_apellido",
                "especialidad": "$vet_especialidad",
                "sucursal": "$vet_sucursal",
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
            "id_paciente": "$_id",
            "nombre": "$paciente.nombre",
            "especie": "$paciente.especie",
            "raza": "$paciente.raza",
            "fecha_nac": "$paciente.fecha_nac",
            "id_propietario": "$paciente.id_propietario",
            "activo": "$paciente.activo",
            "veterinarios": 1,
        }},
        {"$sort": {"id_paciente": 1}},
    ]
    return list(db.consultas.aggregate(pipeline))
