"""Modelos Pydantic para validar los cuerpos de los endpoints que mutan datos.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConsultaIn(BaseModel):
    id_paciente: str
    id_vet: str
    motivo: str
    diagnostico: str
    costo: float = Field(ge=0)
    estado: str = "Cerrada"
    fecha: datetime | None = None          # Pydantic parsea "2026-06-08" -> datetime
    id_consulta: str                       # obligatorio: lo provee quien llama (→ 422 si falta)


class PropietarioIn(BaseModel):
    id_propietario: str
    nombre: str
    apellido: str
    dni: str
    email: str
    telefono: str
    ciudad: str
    provincia: str
    activo: bool = True


class PropietarioUpdate(BaseModel):        # todo opcional: es un PUT parcial
    nombre: str | None = None
    apellido: str | None = None
    dni: str | None = None
    email: str | None = None
    telefono: str | None = None
    ciudad: str | None = None
    provincia: str | None = None
    activo: bool | None = None


class StockDecrementoIn(BaseModel):
    cantidad: int = Field(gt=0)            # mata el KeyError y exige positivo
