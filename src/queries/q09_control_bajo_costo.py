"""Consulta 9 — Consultas de tipo 'Control' con costo menor a $5.000.

Motor: MongoDB. Técnica: `find(motivo="Control", costo < 5000)`.
"""

from __future__ import annotations

from src.db.mongo import get_db
from src.queries._util import print_result


def consultas_control_bajo_costo(umbral: float = 5000) -> list[dict]:
    """Devuelve las consultas de motivo 'Control' con costo menor al umbral."""
    db = get_db()
    cursor = db.consultas.find(
        {"motivo": "Control", "costo": {"$lt": umbral}},
        {"_id": 0, "id_consulta": 1, "id_paciente": 1, "id_vet": 1,
         "fecha": 1, "motivo": 1, "diagnostico": 1, "costo": 1},
    ).sort("costo", 1)
    return list(cursor)


if __name__ == "__main__":  # pragma: no cover
    print_result("Consulta 9 - Controles con costo < $5.000",
                 consultas_control_bajo_costo())
