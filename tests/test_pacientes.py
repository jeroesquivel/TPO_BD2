from tests.conftest import REF


# --- q01 ---

def test_q01_devuelve_solo_activos(client):
    r = client.get("/pacientes/activos")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 17
    ids = {p["id_paciente"] for p in data}
    # inactivos no deben aparecer
    assert "P003" not in ids
    assert "P014" not in ids
    assert "P020" not in ids

def test_q01_incluye_datos_propietario(client):
    r = client.get("/pacientes/activos")
    p = next(x for x in r.json() if x["id_paciente"] == "P001")
    # el join con propietarios debe estar presente
    assert "propietario" in p or "nombre_propietario" in p or "id_propietario" in p


# --- q03 ---

def test_q03_historial_p001_tiene_cinco_eventos(client):
    r = client.get("/pacientes/P001/historial")
    assert r.status_code == 200
    eventos = r.json()
    # 3 consultas (CON001, CON007, CON025) + 2 vacunaciones (VAC001, VAC002)
    assert len(eventos) == 5

def test_q03_historial_ordenado_por_fecha(client):
    r = client.get("/pacientes/P001/historial")
    fechas = [e["fecha"] for e in r.json()]
    assert fechas == sorted(fechas)

def test_q03_historial_incluye_tipos(client):
    r = client.get("/pacientes/P001/historial")
    tipos = {e["tipo"] for e in r.json()}
    assert "Consulta" in tipos
    assert "Vacunación" in tipos

def test_q03_paciente_inexistente_devuelve_lista_vacia(client):
    r = client.get("/pacientes/PXXX/historial")
    assert r.status_code == 200
    assert r.json() == []


# --- q06 ---

def test_q06_vacunas_vencidas_son_cinco(client):
    r = client.get("/pacientes/vacunas-vencidas", params={"referencia": REF})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 5
    ids = {v["id_vacuna"] for v in data}
    assert ids == {"VAC007", "VAC008", "VAC009", "VAC010", "VAC015"}

def test_q06_no_incluye_vacunas_futuras(client):
    r = client.get("/pacientes/vacunas-vencidas", params={"referencia": REF})
    ids = {v["id_vacuna"] for v in r.json()}
    # VAC011..VAC014, VAC016: próxima dosis futura
    assert not ids.intersection({"VAC011", "VAC012", "VAC013", "VAC014", "VAC016"})


# --- q10 ---

def test_q10_palermo_devuelve_cuatro_pacientes(client):
    r = client.get("/pacientes/por-sucursal", params={"sucursal": "Palermo"})
    assert r.status_code == 200
    data = r.json()
    # Vets Palermo: V001, V003, V011, V016 → pacientes únicos: P001, P002, P006, P013
    assert len(data) == 4
    ids = {p["id_paciente"] for p in data}
    assert ids == {"P001", "P002", "P006", "P013"}

def test_q10_sucursal_sin_actividad_devuelve_lista_vacia(client):
    r = client.get("/pacientes/por-sucursal", params={"sucursal": "SucursalInventada"})
    assert r.status_code == 200
    assert r.json() == []
