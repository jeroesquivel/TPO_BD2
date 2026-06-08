from tests.conftest import REF


# --- q02 ---

def test_q02_ocho_consultas_seguimiento(client):
    r = client.get("/consultas/seguimiento")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 8
    ids = {c["id_consulta"] for c in data}
    assert "CON004" in ids
    assert "CON022" in ids

def test_q02_incluye_vet_y_costo(client):
    r = client.get("/consultas/seguimiento")
    c = r.json()[0]
    assert "veterinario" in c or "id_vet" in c
    assert "costo" in c


# --- q05 ---

def test_q05_incluye_vets_con_cero_consultas(client):
    r = client.get("/consultas/vets-activos", params={"referencia": REF})
    assert r.status_code == 200
    data = r.json()
    cero = [v for v in data if v["consultas_60d"] == 0]
    # V002, V009, V011, V014, V016 no tienen consultas en el período
    ids_cero = {v["id_vet"] for v in cero}
    assert {"V002", "V009", "V011", "V014", "V016"}.issubset(ids_cero)

def test_q05_vet_con_mas_consultas(client):
    r = client.get("/consultas/vets-activos", params={"referencia": REF})
    data = r.json()
    top = data[0]  # ordenado desc
    # V006 tiene 4 consultas en el período
    assert top["id_vet"] == "V006"
    assert top["consultas_60d"] == 4

def test_q05_solo_activos(client):
    r = client.get("/consultas/vets-activos", params={"referencia": REF})
    ids = {v["id_vet"] for v in r.json()}
    # V004 y V010 son inactivos
    assert "V004" not in ids
    assert "V010" not in ids


# --- q07 ---

def test_q07_devuelve_cinco_diagnosticos(client):
    r = client.get("/consultas/top-diagnosticos")
    assert r.status_code == 200
    assert len(r.json()) == 5

def test_q07_primer_diagnostico_es_sano(client):
    r = client.get("/consultas/top-diagnosticos")
    top = r.json()[0]
    assert top["diagnostico"] == "Sano"
    assert top["cantidad"] == 6

def test_q07_limite_personalizado(client):
    r = client.get("/consultas/top-diagnosticos", params={"limite": 3})
    assert len(r.json()) == 3


# --- q09 ---

def test_q09_siete_controles_bajo_costo(client):
    r = client.get("/consultas/control-bajo-costo")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 7

def test_q09_primer_resultado_es_el_mas_barato(client):
    r = client.get("/consultas/control-bajo-costo")
    primero = r.json()[0]
    assert primero["id_consulta"] == "CON007"   # costo 2000
    assert primero["costo"] == 2000

def test_q09_no_incluye_consultas_no_control(client):
    r = client.get("/consultas/control-bajo-costo")
    for c in r.json():
        motivo = c["motivo"].lower()
        assert motivo.startswith("control")

def test_q09_no_incluye_costos_mayores_al_umbral(client):
    r = client.get("/consultas/control-bajo-costo")
    for c in r.json():
        assert c["costo"] < 5000


# --- q11 ---

def test_q11_ingresos_junio_cuatro_vets(client):
    r = client.get("/consultas/ingresos-por-vet", params={"referencia": REF})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4

def test_q11_ingresos_correctos(client):
    r = client.get("/consultas/ingresos-por-vet", params={"referencia": REF})
    por_vet = {v["id_vet"]: v["total_ingresos"] for v in r.json()}
    assert por_vet["V003"] == 6800
    assert por_vet["V006"] == 5300
    assert por_vet["V001"] == 4000
    assert por_vet["V013"] == 3400


# --- q14 ---

def test_q14_registrar_consulta_valida(client):
    payload = {
        "id_paciente": "P001",
        "id_vet": "V001",
        "fecha": "2026-06-08",
        "motivo": "Test",
        "diagnostico": "Sano",
        "costo": 1000,
        "estado": "Cerrada",
    }
    r = client.post("/consultas", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "id_consulta" in body
    assert body["id_consulta"].startswith("CON")
    # limpieza: borrar la consulta insertada (requiere endpoint DELETE /consultas o
    # bien llamar directamente a la DB en el teardown)

def test_q14_paciente_inexistente_da_404(client):
    r = client.post("/consultas", json={
        "id_paciente": "PXXX", "id_vet": "V001",
        "fecha": "2026-06-08", "motivo": "Test",
        "diagnostico": "Sano", "costo": 1000, "estado": "Cerrada",
    })
    assert r.status_code == 404

def test_q14_vet_inexistente_da_404(client):
    r = client.post("/consultas", json={
        "id_paciente": "P001", "id_vet": "VXXX",
        "fecha": "2026-06-08", "motivo": "Test",
        "diagnostico": "Sano", "costo": 1000, "estado": "Cerrada",
    })
    assert r.status_code == 404
