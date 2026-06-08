from fastapi import APIRouter, Body
from src.api.services import propietarios_service

router = APIRouter(prefix="/propietarios", tags=["propietarios"])


@router.get("/multi-paciente")
def r04():
    return propietarios_service.get_propietarios_multipaciente()


@router.get("/sin-consultas")
def r12():
    return propietarios_service.get_propietarios_sin_consultas()


@router.post("")
def c13(p: dict = Body(...)):
    return propietarios_service.alta_propietario(p)


@router.put("/{id_p}")
def m13(id_p: str, cambios: dict = Body(...)):
    return propietarios_service.modificar_propietario(id_p, cambios)


@router.delete("/{id_p}")
def b13(id_p: str):
    return propietarios_service.baja_propietario(id_p)
