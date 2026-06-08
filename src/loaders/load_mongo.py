
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
    "stock",
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


def _map_consulta(row: dict, vet_by_id: dict, pac_by_id: dict) -> dict:
    vet = vet_by_id.get(clean_str(row["id_vet"]))
    pac = pac_by_id.get(clean_str(row["id_paciente"]))
    if vet is None or pac is None:
        raise ValueError(f"FK inexistente en consulta {row}")
    return {
        "id_consulta": clean_str(row["id_consulta"]),
        "id_paciente": clean_str(row["id_paciente"]),
        "id_vet": clean_str(row["id_vet"]),
        "fecha": parse_date(row["fecha"]),
        "motivo": clean_str(row["motivo"]),
        "diagnostico": clean_str(row["diagnostico"]),
        "costo": parse_number(row["costo"]),
        "estado": clean_str(row["estado"]),
        "vet_nombre": vet["nombre"],
        "vet_apellido": vet["apellido"],
        "vet_especialidad": vet["especialidad"],
        "vet_sucursal": vet["sucursal"],
        "id_propietario": pac["id_propietario"],
    }


def _map_producto(row: dict) -> dict:
    return {
        "id_producto": clean_str(row["id_producto"]),
        "nombre": clean_str(row["nombre"]),
        "categoria": normalize_categoria(row["categoria"]),
        "unidades": parse_number(row["unidades"]),
        "precio_unit": parse_number(row["precio_unit"]),
        "vencimiento": parse_date(row["vencimiento"]),
        "proveedor": clean_str(row["proveedor"]),
    }


def _map_vacunacion(row: dict, vet_by_id: dict) -> dict:
    vet = vet_by_id.get(clean_str(row["id_vet"]))
    if vet is None:
        raise ValueError(f"FK inexistente en vacunación {row}")
    return {
        "id_vacuna": clean_str(row["id_vacuna"]),
        "id_paciente": clean_str(row["id_paciente"]),
        "id_vet": clean_str(row["id_vet"]),
        "fecha_aplicacion": parse_date(row["fecha_aplicacion"]),
        "nombre_vacuna": clean_str(row["nombre_vacuna"]),
        "proxima_dosis": parse_date(row["proxima_dosis"]),
        "vet_nombre": vet["nombre"],
        "vet_apellido": vet["apellido"],
        "vet_especialidad": vet["especialidad"],
        "vet_sucursal": vet["sucursal"],
    }


def _create_indexes(db) -> None:
    db.pacientes.create_index([("id_paciente", ASCENDING)], unique=True)
    db.pacientes.create_index([("id_propietario", ASCENDING)])
    db.propietarios.create_index([("id_propietario", ASCENDING)], unique=True)
    db.veterinarios.create_index([("id_vet", ASCENDING)], unique=True)
    db.consultas.create_index([("id_consulta", ASCENDING)], unique=True)
    db.consultas.create_index([("id_paciente", ASCENDING)])
    db.consultas.create_index([("id_vet", ASCENDING)])
    db.consultas.create_index([("fecha", ASCENDING)])
    db.consultas.create_index([("vet_sucursal", ASCENDING)])
    db.consultas.create_index([("id_propietario", ASCENDING)])
    db.vacunaciones.create_index([("id_vacuna", ASCENDING)], unique=True)
    db.vacunaciones.create_index([("id_paciente", ASCENDING)])
    db.vacunaciones.create_index([("proxima_dosis", ASCENDING)])
    db.cirugias.create_index([("id_cirugia", ASCENDING)], unique=True)
    db.stock.create_index([("id_producto", ASCENDING)], unique=True)
    db.stock.create_index([("unidades", ASCENDING)])
    db.stock.create_index([("vencimiento", ASCENDING)])


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
    vet_by_id = {v["id_vet"]: v for v in veterinarios}
    pac_by_id = {p["id_paciente"]: p for p in pacientes}
    consultas = [_map_consulta(r, vet_by_id, pac_by_id) for r in _read_csv("consultas.csv")]
    vacunaciones = [_map_vacunacion(r, vet_by_id) for r in _read_csv("vacunaciones.csv")]
    stock = [_map_producto(r) for r in _read_csv("stock_farmaceutico.csv")]

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
    if stock:
        db.stock.insert_many(stock)

    _create_indexes(db)

    counts = {
        "propietarios": len(propietarios),
        "veterinarios": len(veterinarios),
        "pacientes": len(pacientes),
        "consultas": len(consultas),
        "vacunaciones": len(vacunaciones),
        "stock": len(stock),
    }
    return counts


__all__ = ["load"]


if __name__ == "__main__":  # pragma: no cover
    result = load()
    print("ETL MongoDB completado:")
    for coll, n in result.items():
        print(f"  - {coll}: {n} documentos")
