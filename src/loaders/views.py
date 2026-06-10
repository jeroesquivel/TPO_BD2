"""Vistas de MongoDB para VetSalud.
"""

from __future__ import annotations

from pymongo.database import Database

from src.db.mongo import get_db
from src.queries.q11_ingresos_por_vet_mes import VISTA, pipeline_vista


def ensure_vista_ingresos_por_vet(db: Database | None = None) -> None:
    """(Re)crea la vista `vista_ingresos_por_vet` sobre `consultas`.

    Idempotente: si la vista ya existe la elimina y la vuelve a crear, de modo que
    el pipeline quede siempre sincronizado con el código.
    """
    db = db if db is not None else get_db()
    if VISTA in db.list_collection_names():
        db.drop_collection(VISTA)
    db.create_collection(VISTA, viewOn="consultas", pipeline=pipeline_vista())


def ensure_views(db: Database | None = None) -> list[str]:
    """Crea todas las vistas del proyecto. Devuelve los nombres creados."""
    db = db if db is not None else get_db()
    ensure_vista_ingresos_por_vet(db)
    return [VISTA]


__all__ = ["ensure_views", "ensure_vista_ingresos_por_vet", "VISTA"]


if __name__ == "__main__":  # pragma: no cover
    nombres = ensure_views()
    print("Vistas creadas:", ", ".join(nombres))
