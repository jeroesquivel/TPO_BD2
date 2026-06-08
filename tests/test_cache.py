import redis


# helpers
def cache_keys(redis) -> set:
    return set(redis.keys("cache:*"))


def _redis_caido(*_a, **_k):
    raise redis.exceptions.ConnectionError("redis caído (simulado)")


# --- cache miss → hit ---

def test_cache_miss_luego_hit_q01(client, redis):
    assert not any(k.startswith("cache:q01") for k in cache_keys(redis))

    r1 = client.get("/pacientes/activos")
    assert r1.status_code == 200
    assert any(k.startswith("cache:q01") for k in cache_keys(redis))   # miss → cacheado

    r2 = client.get("/pacientes/activos")
    assert r2.json() == r1.json()   # hit: mismo resultado

def test_cache_miss_luego_hit_q07(client, redis):
    client.get("/consultas/top-diagnosticos")
    assert any(k.startswith("cache:q07") for k in cache_keys(redis))

def test_cache_q07_clave_incluye_parametro(client, redis):
    client.get("/consultas/top-diagnosticos", params={"limite": 3})
    client.get("/consultas/top-diagnosticos", params={"limite": 5})
    claves = cache_keys(redis)
    assert any("q07:3" in k for k in claves)
    assert any("q07:5" in k for k in claves)

def test_cache_q03_clave_incluye_id_paciente(client, redis):
    client.get("/pacientes/P001/historial")
    client.get("/pacientes/P002/historial")
    claves = cache_keys(redis)
    assert any("q03:P001" in k for k in claves)
    assert any("q03:P002" in k for k in claves)


# --- invalidación por escritura en propietarios ---

def test_invalidacion_post_propietario_limpia_q01_q04_q12(client, redis):
    # poblar caché
    client.get("/pacientes/activos")
    client.get("/propietarios/multi-paciente")
    client.get("/propietarios/sin-consultas")
    assert any(k.startswith("cache:q01") for k in cache_keys(redis))
    assert any(k.startswith("cache:q04") for k in cache_keys(redis))
    assert any(k.startswith("cache:q12") for k in cache_keys(redis))

    # escribir
    nuevo = {"id_propietario": "CINV", "nombre": "Inv", "apellido": "Test",
             "dni": "11111111", "email": "inv@test.com", "telefono": "1111111111",
             "ciudad": "X", "provincia": "Y"}
    client.post("/propietarios", json=nuevo)

    claves = cache_keys(redis)
    assert not any(k.startswith("cache:q01") for k in claves)
    assert not any(k.startswith("cache:q04") for k in claves)
    assert not any(k.startswith("cache:q12") for k in claves)

    client.delete("/propietarios/CINV")


# --- invalidación por escritura en consultas ---

def test_invalidacion_post_consulta_limpia_claves_afectadas(client, redis):
    # poblar caché de todas las queries afectadas
    client.get("/consultas/seguimiento")                                    # q02
    client.get("/pacientes/P001/historial")                                 # q03:P001
    client.get("/consultas/vets-activos")                                   # q05
    client.get("/consultas/top-diagnosticos")                               # q07
    client.get("/consultas/control-bajo-costo")                             # q09
    client.get("/pacientes/por-sucursal", params={"sucursal": "Palermo"})   # q10
    client.get("/consultas/ingresos-por-vet")                               # q11
    client.get("/propietarios/sin-consultas")                               # q12

    antes = cache_keys(redis)
    assert any(k.startswith("cache:q02") for k in antes)
    assert any(k.startswith("cache:q03") for k in antes)

    # registrar nueva consulta (P001 activo, V001 activo)
    r = client.post("/consultas", json={
        "id_paciente": "P001", "id_vet": "V001",
        "fecha": "2026-06-08", "motivo": "Control test",
        "diagnostico": "Sano", "costo": 1500, "estado": "Cerrada",
    })
    assert r.status_code == 200

    despues = cache_keys(redis)
    for prefijo in ["q02", "q03", "q05", "q07", "q09", "q10", "q11", "q12"]:
        assert not any(k.startswith(f"cache:{prefijo}") for k in despues), \
            f"cache:{prefijo}* debería haber sido invalidado"


# --- invalidación por decremento de stock ---

def test_invalidacion_post_stock_limpia_q08(client, redis):
    client.get("/stock/bajo")
    assert any(k.startswith("cache:q08") for k in cache_keys(redis))

    client.post("/stock/PRD005/decrementar", json={"cantidad": 1})

    assert not any(k.startswith("cache:q08") for k in cache_keys(redis))


# --- q08 no es afectado por escritura en consultas ---

def test_post_consulta_no_invalida_q08(client, redis):
    client.get("/stock/bajo")
    assert any(k.startswith("cache:q08") for k in cache_keys(redis))

    client.post("/consultas", json={
        "id_paciente": "P001", "id_vet": "V001",
        "fecha": "2026-06-08", "motivo": "Test",
        "diagnostico": "Sano", "costo": 100, "estado": "Cerrada",
    })

    # q08 debe seguir en caché (no fue invalidado)
    assert any(k.startswith("cache:q08") for k in cache_keys(redis))


# --- q01 no es afectado por escritura en consultas ---

def test_post_consulta_no_invalida_q01(client, redis):
    client.get("/pacientes/activos")
    claves_antes = cache_keys(redis)
    assert any(k.startswith("cache:q01") for k in claves_antes)

    client.post("/consultas", json={
        "id_paciente": "P001", "id_vet": "V001",
        "fecha": "2026-06-08", "motivo": "Test",
        "diagnostico": "Sano", "costo": 100, "estado": "Cerrada",
    })

    assert any(k.startswith("cache:q01") for k in cache_keys(redis))


# --- caché tolerante a fallos: si Redis cae, la API sigue contra Mongo ---

def test_lectura_degrada_a_mongo_si_redis_cae(client, monkeypatch):
    monkeypatch.setattr("src.db.cache.get_redis", _redis_caido)
    r = client.get("/pacientes/activos")
    assert r.status_code == 200
    assert len(r.json()) == 17   # mismos datos que servidos con caché

def test_escritura_no_falla_si_redis_cae(client, monkeypatch):
    # La consulta commitea en Mongo; invalidar es best-effort y no debe tumbar la
    # request (si lo hiciera, un retry duplicaría la consulta).
    monkeypatch.setattr("src.db.cache.get_redis", _redis_caido)
    r = client.post("/consultas", json={
        "id_paciente": "P001", "id_vet": "V001",
        "fecha": "2026-06-08", "motivo": "Test redis caído",
        "diagnostico": "Sano", "costo": 1000, "estado": "Cerrada",
    })
    assert r.status_code == 200
    assert r.json()["id_consulta"].startswith("CON")
    # la consulta insertada la limpia el fixture autouse `restaura_db`
