import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.cache import flush_cache
from src.db.mongo import get_db
from src.db.redis_client import get_redis


REF = "2026-06-01"   # fecha congelada con freeze_time en los tests de q05/q06/q11/q12


@pytest.fixture(scope="session")
def client():
    """TestClient de sesión: levanta la app en proceso, sin servidor externo."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def limpia_cache():
    """Vacía Redis antes de cada test para aislar comportamiento de caché."""
    flush_cache()
    yield
    flush_cache()


@pytest.fixture(autouse=True)
def restaura_db():
    """Restaura las colecciones mutables tras cada test, para que las pruebas sean
    independientes del orden. Varios tests (caché y servicios) insertan consultas o
    propietarios y decrementan stock; sin esto contaminarían los conteos de otros.
    """
    db = get_db()
    consultas = set(db.consultas.distinct("id_consulta"))
    propietarios = {d["id_propietario"]: d for d in db.propietarios.find({}, {"_id": 0})}
    stock = {d["id_producto"]: d["unidades"]
             for d in db.stock.find({}, {"_id": 0, "id_producto": 1, "unidades": 1})}
    yield
    # consultas: borrar las creadas durante el test
    db.consultas.delete_many({"id_consulta": {"$nin": list(consultas)}})
    # propietarios: borrar nuevos y restaurar los modificados
    despues = {d["id_propietario"]: d for d in db.propietarios.find({}, {"_id": 0})}
    nuevos = list(set(despues) - set(propietarios))
    if nuevos:
        db.propietarios.delete_many({"id_propietario": {"$in": nuevos}})
    for pid, doc in propietarios.items():
        if despues.get(pid) != doc:
            db.propietarios.replace_one({"id_propietario": pid}, doc)
    # stock: restaurar unidades
    for pid, unidades in stock.items():
        db.stock.update_one({"id_producto": pid}, {"$set": {"unidades": unidades}})


@pytest.fixture
def redis():
    return get_redis()
