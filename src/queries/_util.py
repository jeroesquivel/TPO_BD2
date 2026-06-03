"""Utilidades compartidas por los módulos de consulta (impresión de ejemplos)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Iterable

# En consolas Windows (cp1252) los acentos se ven como "�"; forzamos UTF-8 para
# que la salida de ejemplo sea legible. Los datos en la base ya están en UTF-8.
try:  # pragma: no cover - depende de la plataforma
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def _default(value):
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)


def print_result(title: str, rows: Iterable) -> None:
    """Imprime un encabezado y las filas de una consulta de forma legible."""
    rows = list(rows)
    print(f"\n=== {title} ({len(rows)} resultado/s) ===")
    for row in rows:
        if isinstance(row, dict):
            row = {k: v for k, v in row.items() if k != "_id"}
            print(json.dumps(row, ensure_ascii=False, default=_default))
        else:
            print(row)
