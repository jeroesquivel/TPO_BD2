"""Consulta 11 — Vista agregada: ingresos totales por veterinario en el mes actual.


"""

from __future__ import annotations

from datetime import datetime

from src.db.mongo import get_db

# Nombre de la vista de MongoDB que respalda esta consulta (la crea el loader).
VISTA = "vista_ingresos_por_vet"

# Etapas posteriores al `$match`: idénticas para la vista (mes dinámico vía $$NOW)
# y para la agregación parametrizada por un mes fijo (pruebas/demos deterministas).
_ETAPAS_AGREGACION = [
    {"$group": {
        "_id": "$id_vet",
        "vet_nombre":       {"$first": "$vet_nombre"},
        "vet_apellido":     {"$first": "$vet_apellido"},
        "vet_especialidad": {"$first": "$vet_especialidad"},
        "vet_sucursal":     {"$first": "$vet_sucursal"},
        "ingresos":         {"$sum": "$costo"},
    }},
    {"$project": {
        "_id": 0,
        "id_vet":       "$_id",
        "nombre":       "$vet_nombre",
        "apellido":     "$vet_apellido",
        "especialidad": "$vet_especialidad",
        "sucursal":     "$vet_sucursal",
        "ingresos": 1,
    }},
    {"$sort": {"ingresos": -1}},
]


def pipeline_vista() -> list[dict]:
    """Pipeline que respalda la vista: ingresos del mes en curso resuelto con `$$NOW`.
    El `$match` compara año+mes de cada `fecha` contra los de `$$NOW`, de modo que
    la vista refleja siempre el mes vigente en el reloj del servidor MongoDB.
    """
    match_mes_actual = {"$match": {"$expr": {"$and": [
        {"$eq": [{"$year": "$fecha"}, {"$year": "$$NOW"}]},
        {"$eq": [{"$month": "$fecha"}, {"$month": "$$NOW"}]},
    ]}}}
    return [match_mes_actual, *_ETAPAS_AGREGACION]


def _rango_mes_actual(referencia: datetime) -> tuple[datetime, datetime]:
    inicio = referencia.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)
    return inicio, fin


def ingresos_por_vet_mes_actual(referencia: datetime | None = None) -> list[dict]:
    """Ingresos totales por veterinario en el mes en curso.
    """
    db = get_db()
    if referencia is None:
        return list(db[VISTA].find({}, {"_id": 0}))
    inicio, fin = _rango_mes_actual(referencia)
    pipeline = [{"$match": {"fecha": {"$gte": inicio, "$lt": fin}}}, *_ETAPAS_AGREGACION]
    return list(db.consultas.aggregate(pipeline))
