

from __future__ import annotations

from datetime import datetime


def clean_str(value) -> str:
    """Quita espacios sobrantes y normaliza a string."""
    return str(value).strip() if value is not None else ""


def parse_bool(value) -> bool:
    """Convierte `"True"/"False"` (o bool) a un `bool` de Python."""
    if isinstance(value, bool):
        return value
    return clean_str(value).lower() in ("true", "1", "si", "sí", "yes")


def parse_date(value) -> datetime | None:
    """Convierte un string `YYYY-MM-DD` a `datetime`. Devuelve None si vacío."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = clean_str(value)
    if not text:
        return None
    return datetime.strptime(text, "%Y-%m-%d")


def parse_number(value):
    """Convierte a `int` o `float` según corresponda. Devuelve None si vacío."""
    text = clean_str(value)
    if not text:
        return None
    number = float(text)
    return int(number) if number.is_integer() else number


def normalize_categoria(value) -> str:
    """Normaliza categorías: quita el punto final sobrante (`"Antiparasitario."`)."""
    return clean_str(value).rstrip(".").strip()
