from fastapi import APIRouter

from src.api.services import pacientes_service

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


@router.get("/activos")
def r01():
    return pacientes_service.get_pacientes_activos()


@router.get("/vacunas-vencidas")
def r06():
    return pacientes_service.get_vacunas_vencidas()


@router.get("/por-sucursal")
def r10(sucursal: str):
    return pacientes_service.get_pacientes_por_sucursal(sucursal)


@router.get("/{id_paciente}/historial")
def r03(id_paciente: str):
    return pacientes_service.get_historial(id_paciente)


@router.get("/{id_paciente}/historial-completo")
def r03_completo(id_paciente: str):
    """Extra historial + cirugías."""
    return pacientes_service.get_historial_completo(id_paciente)
