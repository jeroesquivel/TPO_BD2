from fastapi import APIRouter

from src.api.models import PropietarioIn, PropietarioUpdate
from src.api.services import propietarios_service

router = APIRouter(prefix="/propietarios", tags=["propietarios"])


@router.get("/multi-paciente")
def r04():
    return propietarios_service.get_propietarios_multipaciente()


@router.get("/sin-consultas")
def r12():
    return propietarios_service.get_propietarios_sin_consultas()


@router.post("")
def c13(p: PropietarioIn):
    return propietarios_service.alta_propietario(p.model_dump())


@router.put("/{id_p}")
def m13(id_p: str, cambios: PropietarioUpdate):
    return propietarios_service.modificar_propietario(id_p, cambios.model_dump(exclude_none=True))


@router.delete("/{id_p}")
def b13(id_p: str):
    return propietarios_service.baja_propietario(id_p)
