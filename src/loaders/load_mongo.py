"""ETL CSV -> MongoDB para VetSalud.

Lee los CSV de `data/`, aplica las reglas de limpieza (sección 7) e inserta los
documentos en las colecciones correspondientes, creando además los índices
sugeridos (sección 6). El orden de carga respeta las dependencias entre
entidades: propietarios y veterinarios primero, luego pacientes, y por último
consultas y vacunaciones.

Las fechas se almacenan como `datetime` y los montos como números, requisito
indispensable para los filtros temporales y las sumas de las consultas.
"""

from __future__ import annotations

import csv
from pathlib import Path

from pymongo import ASCENDING

from src.db.mongo import get_db
from src.loaders.clean import (
    clean_str,
    normalize_categoria,
    parse_bool,
    parse_date,
    parse_number,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

COLLECTIONS = (
    "pacientes",
    "propietarios",
    "veterinarios",
    "consultas",
    "vacunaciones",
    "cirugias",
)


def _read_csv(filename: str) -> list[dict]:
    """Lee un CSV de `data/` y devuelve la lista de filas como dicts."""
    path = DATA_DIR / filename
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _map_propietario(row: dict) -> dict:
    return {
        "id_propietario": clean_str(row["id_propietario"]),
        "nombre": clean_str(row["nombre"]),
        "apellido": clean_str(row["apellido"]),
        "dni": clean_str(row["dni"]),
        "email": clean_str(row["email"]),
        "telefono": clean_str(row["telefono"]),
        "ciudad": clean_str(row["ciudad"]),
        "provincia": clean_str(row["provincia"]),
        # El CSV base no trae `activo`; por defecto los propietarios están activos.
        "activo": parse_bool(row.get("activo", "True")),
    }


def _map_veterinario(row: dict) -> dict:
    return {
        "id_vet": clean_str(row["id_vet"]),
        "nombre": clean_str(row["nombre"]),
        "apellido": clean_str(row["apellido"]),
        "matricula": clean_str(row["matricula"]),
        "especialidad": clean_str(row["especialidad"]),
        "sucursal": clean_str(row["sucursal"]),
        "activo": parse_bool(row["activo"]),
    }


def _map_paciente(row: dict) -> dict:
    return {
        "id_paciente": clean_str(row["id_paciente"]),
        "nombre": clean_str(row["nombre"]),
        "especie": clean_str(row["especie"]),
        "raza": clean_str(row["raza"]),
        "fecha_nac": parse_date(row["fecha_nac"]),
        "id_propietario": clean_str(row["id_propietario"]),
        "activo": parse_bool(row["activo"]),
    }


def _map_consulta(row: dict) -> dict:
    return {
        "id_consulta": clean_str(row["id_consulta"]),
        "id_paciente": clean_str(row["id_paciente"]),
        "id_vet": clean_str(row["id_vet"]),
        "fecha": parse_date(row["fecha"]),
        "motivo": clean_str(row["motivo"]),
        "diagnostico": clean_str(row["diagnostico"]),
        "costo": parse_number(row["costo"]),
        "estado": clean_str(row["estado"]),
    }


def _map_vacunacion(row: dict) -> dict:
    return {
        "id_vacuna": clean_str(row["id_vacuna"]),
        "id_paciente": clean_str(row["id_paciente"]),
        "id_vet": clean_str(row["id_vet"]),
        "fecha_aplicacion": parse_date(row["fecha_aplicacion"]),
        "nombre_vacuna": clean_str(row["nombre_vacuna"]),
        "proxima_dosis": parse_date(row["proxima_dosis"]),
    }


def _create_indexes(db) -> None:
    """Crea los índices sugeridos en la sección 6 de la guía."""
    db.pacientes.create_index([("id_paciente", ASCENDING)], unique=True)
    db.pacientes.create_index([("id_propietario", ASCENDING)])
    db.propietarios.create_index([("id_propietario", ASCENDING)], unique=True)
    db.veterinarios.create_index([("id_vet", ASCENDING)], unique=True)
    db.consultas.create_index([("id_consulta", ASCENDING)], unique=True)
    db.consultas.create_index([("id_paciente", ASCENDING)])
    db.consultas.create_index([("id_vet", ASCENDING)])
    db.consultas.create_index([("fecha", ASCENDING)])
    db.vacunaciones.create_index([("id_vacuna", ASCENDING)], unique=True)
    db.vacunaciones.create_index([("id_paciente", ASCENDING)])
    db.vacunaciones.create_index([("proxima_dosis", ASCENDING)])
    db.cirugias.create_index([("id_cirugia", ASCENDING)], unique=True)


def load(drop: bool = True) -> dict[str, int]:
    """Ejecuta el ETL base hacia MongoDB.

    Args:
        drop: si es True, vacía las colecciones antes de cargar (carga idempotente).

    Returns:
        Diccionario con la cantidad de documentos insertados por colección.
    """
    db = get_db()

    if drop:
        for coll in COLLECTIONS:
            db[coll].drop()

    propietarios = [_map_propietario(r) for r in _read_csv("propietarios.csv")]
    veterinarios = [_map_veterinario(r) for r in _read_csv("veterinarios.csv")]
    pacientes = [_map_paciente(r) for r in _read_csv("pacientes.csv")]
    consultas = [_map_consulta(r) for r in _read_csv("consultas.csv")]
    vacunaciones = [_map_vacunacion(r) for r in _read_csv("vacunaciones.csv")]

    counts: dict[str, int] = {}
    if propietarios:
        db.propietarios.insert_many(propietarios)
    if veterinarios:
        db.veterinarios.insert_many(veterinarios)
    if pacientes:
        db.pacientes.insert_many(pacientes)
    if consultas:
        db.consultas.insert_many(consultas)
    if vacunaciones:
        db.vacunaciones.insert_many(vacunaciones)

    _create_indexes(db)

    counts = {
        "propietarios": len(propietarios),
        "veterinarios": len(veterinarios),
        "pacientes": len(pacientes),
        "consultas": len(consultas),
        "vacunaciones": len(vacunaciones),
    }
    return counts


# La normalización de categoría se usa en el loader de Redis; se reexporta aquí
# para que el ETL completo comparta las mismas reglas de limpieza.
__all__ = ["load", "normalize_categoria"]


if __name__ == "__main__":  # pragma: no cover
    result = load()
    print("ETL MongoDB completado:")
    for coll, n in result.items():
        print(f"  - {coll}: {n} documentos")
