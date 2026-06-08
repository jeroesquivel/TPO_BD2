from fastapi import APIRouter, Body
from src.api.services import stock_service

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/bajo")
def r08(umbral: int = 50):
    return stock_service.get_stock_bajo(umbral)


@router.post("/{id_producto}/decrementar")
def c15(id_producto: str, body: dict = Body(...)):
    return stock_service.decrementar_stock(id_producto, body["cantidad"])
