from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from src.api.routers import consultas, pacientes, propietarios, stock
from src.queries.q13_abm_propietarios import PropietarioDuplicadoError
from src.queries.q14_registrar_consulta import ValidacionError
from src.queries.q15_decrementar_stock import StockError

app = FastAPI(title="VetSalud API")


@app.exception_handler(StockError)
async def _stock_handler(_, exc: StockError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(PropietarioDuplicadoError)
async def _duplicado_handler(_, exc: PropietarioDuplicadoError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ValidacionError)
async def _validacion_handler(_, exc: ValidacionError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/health", tags=["health"])
def health():
    return {"ok": True}


app.include_router(pacientes.router)
app.include_router(propietarios.router)
app.include_router(consultas.router)
app.include_router(stock.router)
