"""Consulta 13 — ABM completo de propietarios: alta, modificación y baja lógica.

Motor: MongoDB. Técnica: `insert_one` (alta real, falla si el id ya existe),
`update_one` con `$set` (modificación) y baja lógica con `{activo: False}`. Es un
servicio que muta datos: deja el estado consistente y permite mostrar un
antes/después.
"""

from __future__ import annotations

from pymongo import ReturnDocument

from src.db.mongo import get_db
from src.queries._util import print_result


class PropietarioDuplicadoError(ValueError):
    """Se intentó dar de alta un `id_propietario` que ya existe."""


def alta_propietario(propietario: dict) -> dict:
    """Da de alta un propietario nuevo. Devuelve el documento creado.

    Es un alta real (no idempotente): si el `id_propietario` ya existe lanza
    `PropietarioDuplicadoError`. El propietario nace activo si no se indica lo
    contrario.
    """
    db = get_db()
    pid = propietario["id_propietario"]
    if db.propietarios.find_one({"id_propietario": pid}, {"_id": 1}):
        raise PropietarioDuplicadoError(f"El propietario {pid} ya existe")
    doc = {"activo": True, **propietario}
    db.propietarios.insert_one(doc)
    doc.pop("_id", None)
    return doc


def modificar_propietario(id_propietario: str, cambios: dict) -> dict | None:
    """Modifica los datos de un propietario y devuelve el documento ya actualizado.

    Devuelve `None` si el `id_propietario` no existe.
    """
    db = get_db()
    cambios = {k: v for k, v in cambios.items() if k != "id_propietario"}
    return db.propietarios.find_one_and_update(
        {"id_propietario": id_propietario},
        {"$set": cambios},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )


def baja_logica_propietario(id_propietario: str) -> dict | None:
    """Baja lógica: marca `activo=False` sin borrar el documento.

    Devuelve el documento ya actualizado (con `activo=False`), o `None` si el
    `id_propietario` no existe.
    """
    db = get_db()
    return db.propietarios.find_one_and_update(
        {"id_propietario": id_propietario},
        {"$set": {"activo": False}},
        projection={"_id": 0},
        return_document=ReturnDocument.AFTER,
    )


def obtener_propietario(id_propietario: str) -> dict | None:
    """Lectura auxiliar para mostrar el estado antes/después."""
    return get_db().propietarios.find_one(
        {"id_propietario": id_propietario}, {"_id": 0})


if __name__ == "__main__":  # pragma: no cover
    nuevo = {
        "id_propietario": "C999", "nombre": "Demo", "apellido": "Prueba",
        "dni": "99999999", "email": "demo@vetsalud.com", "telefono": "1100000000",
        "ciudad": "CABA", "provincia": "Buenos Aires",
    }
    alta_propietario(nuevo)
    print_result("Consulta 13 - Alta", [obtener_propietario("C999")])
    modificar_propietario("C999", {"email": "demo.nuevo@vetsalud.com",
                                   "telefono": "1122223333"})
    print_result("Consulta 13 - Modificación", [obtener_propietario("C999")])
    baja_logica_propietario("C999")
    print_result("Consulta 13 - Baja lógica", [obtener_propietario("C999")])
