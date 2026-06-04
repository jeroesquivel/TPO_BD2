"""Consulta 13 — ABM completo de propietarios: alta, modificación y baja lógica.

Motor: MongoDB. Técnica: `insert_one` (alta), `update_one` con `$set`
(modificación) y baja lógica con `update_one({activo: False})`. Es un servicio
que muta datos: deja el estado consistente y permite mostrar un antes/después.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def alta_propietario(propietario: dict) -> str:
    """Da de alta un propietario. Devuelve su `id_propietario`.

    El propietario nace activo si no se indica lo contrario.
    """
    db = get_db()
    doc = {"activo": True, **propietario}
    db.propietarios.update_one(
        {"id_propietario": doc["id_propietario"]}, {"$set": doc}, upsert=True)
    return doc["id_propietario"]


def modificar_propietario(id_propietario: str, cambios: dict) -> int:
    """Modifica los datos de un propietario. Devuelve filas modificadas."""
    db = get_db()
    cambios = {k: v for k, v in cambios.items() if k != "id_propietario"}
    res = db.propietarios.update_one(
        {"id_propietario": id_propietario}, {"$set": cambios})
    return res.modified_count


def baja_logica_propietario(id_propietario: str) -> int:
    """Baja lógica: marca `activo=False` sin borrar el documento."""
    db = get_db()
    res = db.propietarios.update_one(
        {"id_propietario": id_propietario}, {"$set": {"activo": False}})
    return res.modified_count


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
