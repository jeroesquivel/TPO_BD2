"""Consulta 14 — Registro de nueva consulta médica con validación de paciente y
veterinario existentes.

Motor: MongoDB. Técnica: verificar la existencia de `id_paciente` e `id_vet` y,
solo si ambos existen, `insert_one` con los campos desnormalizados del vet
(snapshot) para consistencia con las demás consultas.
"""

from __future__ import annotations

from datetime import datetime

from src.db.mongo import get_db
from src.queries._util import print_result


class ValidacionError(ValueError):
    """Error de validación al registrar una consulta (paciente/vet inexistente)."""


def _siguiente_id_consulta(db) -> str:
    """Genera el próximo id_consulta correlativo (CONNNN) usando el máximo numérico."""
    ids = db.consultas.distinct("id_consulta")
    nums = [int(i[3:]) for i in ids if i.startswith("CON") and i[3:].isdigit()]
    return f"CON{(max(nums) + 1) if nums else 1:03d}"


def registrar_consulta(
    id_paciente: str,
    id_vet: str,
    motivo: str,
    diagnostico: str,
    costo: float,
    estado: str = "Cerrada",
    fecha: datetime | None = None,
    id_consulta: str | None = None,
) -> dict:
    """Registra una nueva consulta validando que existan paciente y veterinario.

    Raises:
        ValidacionError: si el paciente o el veterinario no existen.
    """
    db = get_db()
    pac_doc = db.pacientes.find_one({"id_paciente": id_paciente}, {"_id": 0})
    if not pac_doc:
        raise ValidacionError(f"El paciente {id_paciente} no existe")
    vet_doc = db.veterinarios.find_one({"id_vet": id_vet}, {"_id": 0})
    if not vet_doc:
        raise ValidacionError(f"El veterinario {id_vet} no existe")

    doc = {
        "id_consulta":     id_consulta or _siguiente_id_consulta(db),
        "id_paciente":     id_paciente,
        "id_vet":          id_vet,
        "fecha":           fecha or datetime.now(),
        "motivo":          motivo,
        "diagnostico":     diagnostico,
        "costo":           costo,
        "estado":          estado,
        "vet_nombre":      vet_doc["nombre"],
        "vet_apellido":    vet_doc["apellido"],
        "vet_especialidad": vet_doc["especialidad"],
        "vet_sucursal":    vet_doc["sucursal"],
        "id_propietario":  pac_doc["id_propietario"],
    }
    db.consultas.insert_one(doc)
    doc.pop("_id", None)
    return doc


if __name__ == "__main__":  # pragma: no cover
    nueva = registrar_consulta(
        "P001", "V001", "Control de rutina", "Sano", 4300, estado="Cerrada")
    print_result("Consulta 14 - Nueva consulta registrada", [nueva])
    try:
        registrar_consulta("P999", "V001", "x", "y", 100)
    except ValidacionError as exc:
        print(f"\nValidación OK -> {exc}")
