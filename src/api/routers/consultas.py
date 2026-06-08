from fastapi import APIRouter

from src.api.models import ConsultaIn
from src.api.services import consultas_service

router = APIRouter(prefix="/consultas", tags=["consultas"])


@router.get("/seguimiento")
def r02():
    return consultas_service.get_consultas_seguimiento()


@router.get("/vets-activos")
def r05():
    return consultas_service.get_vets_activos()


@router.get("/top-diagnosticos")
def r07(limite: int = 5):
    return consultas_service.get_top_diagnosticos(limite)


@router.get("/control-bajo-costo")
def r09(umbral: float = 5000):
    return consultas_service.get_control_bajo_costo(umbral)


@router.get("/ingresos-por-vet")
def r11():
    return consultas_service.get_ingresos_por_vet()


@router.post("")
def c14(c: ConsultaIn):
    # exclude_none deja que q14 aplique sus defaults (fecha=now, id autogenerado)
    return consultas_service.registrar_consulta(c.model_dump(exclude_none=True))
