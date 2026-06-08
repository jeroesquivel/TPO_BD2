import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.db.cache import flush_cache
from src.db.redis_client import get_redis


REF = "2026-06-01"   # fecha fija para q05/q06/q11/q12


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


@pytest.fixture
def redis():
    return get_redis()
