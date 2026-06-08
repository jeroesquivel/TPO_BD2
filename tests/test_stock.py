# --- q08 ---

def test_q08_seis_productos_bajo_umbral(client):
    r = client.get("/stock/bajo")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 6

def test_q08_incluye_proveedor(client):
    r = client.get("/stock/bajo")
    for p in r.json():
        assert "proveedor" in p

def test_q08_ordenado_ascendente(client):
    r = client.get("/stock/bajo")
    unidades = [p["unidades"] for p in r.json()]
    assert unidades == sorted(unidades)
    assert unidades[0] == 20   # PRD016

def test_q08_primer_resultado_es_prd016(client):
    r = client.get("/stock/bajo")
    assert r.json()[0]["id_producto"] == "PRD016"

def test_q08_umbral_personalizado(client):
    r = client.get("/stock/bajo", params={"umbral": 30})
    # PRD016(20), PRD006(25), PRD011(30) → solo los < 30 = 2
    data = r.json()
    assert len(data) == 2
    for p in data:
        assert p["unidades"] < 30


# --- q15 ---

def test_q15_decremento_exitoso(client):
    # PRD005 tiene 200 unidades (seguro para test)
    r = client.post("/stock/PRD005/decrementar", json={"cantidad": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["unidades_antes"] - body["unidades_despues"] == 1
    # restaurar
    client.post("/stock/PRD005/decrementar", json={"cantidad": -1})   # o directo a DB

def test_q15_stock_insuficiente_da_409(client):
    r = client.post("/stock/PRD016/decrementar", json={"cantidad": 99999})
    assert r.status_code == 409

def test_q15_cantidad_negativa_da_409(client):
    r = client.post("/stock/PRD001/decrementar", json={"cantidad": -5})
    assert r.status_code == 409

def test_q15_producto_inexistente_da_409(client):
    r = client.post("/stock/PRDXXX/decrementar", json={"cantidad": 1})
    assert r.status_code == 409

def test_q15_atomico_no_queda_negativo(client):
    # PRD016 tiene 20 unidades; intentar decrementar 21 → rechazado
    r = client.post("/stock/PRD016/decrementar", json={"cantidad": 21})
    assert r.status_code == 409
    # verificar que unidades no cambiaron
    r2 = client.get("/stock/bajo")
    prd016 = next(p for p in r2.json() if p["id_producto"] == "PRD016")
    assert prd016["unidades"] == 20
