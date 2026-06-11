from freezegun import freeze_time

from tests.conftest import REF


# --- q04 ---

def test_q04_cuatro_propietarios_multipaciente(client):
    r = client.get("/propietarios/multi-paciente")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4
    ids = {p["id_propietario"] for p in data}
    assert ids == {"C001", "C002", "C007", "C017"}


# --- q12 ---

@freeze_time(REF)
def test_q12_propietarios_sin_consultas_ultimo_anio(client):
    r = client.get("/propietarios/sin-consultas")
    assert r.status_code == 200
    data = r.json()
    # C006 (P008 sin consultas), C009, C010 (P012 sin consultas),
    # C011 (última consulta 2024-12), C012, C013, C015
    assert len(data) == 7
    ids = {p["id_propietario"] for p in data}
    assert "C006" in ids    # P008 sin consultas
    assert "C011" in ids    # última consulta antes del corte
    assert "C001" not in ids  # tiene consultas recientes


# --- q13 ABM ---

def test_q13_alta_propietario(client):
    nuevo = {
        "id_propietario": "CTEST",
        "nombre": "Test",
        "apellido": "Prueba",
        "dni": "99999999",
        "email": "test@test.com",
        "telefono": "1199999999",
        "ciudad": "Buenos Aires",
        "provincia": "Buenos Aires",
    }
    r = client.post("/propietarios", json=nuevo)
    assert r.status_code == 200
    # el alta devuelve el documento creado completo (con activo por defecto)
    body = r.json()
    assert body["id_propietario"] == "CTEST"
    assert body["nombre"] == "Test"
    assert body["activo"] is True
    assert "_id" not in body            # no se filtra el ObjectId de Mongo
    # los propietarios de prueba (CTEST*) los limpia el fixture autouse `restaura_db`

def test_q13_modificar_propietario(client):
    nuevo = {"id_propietario": "CTEST2", "nombre": "Mod", "apellido": "Test",
             "dni": "88888888", "email": "mod@test.com", "telefono": "1188888888",
             "ciudad": "Rosario", "provincia": "Santa Fe"}
    client.post("/propietarios", json=nuevo)

    r = client.put("/propietarios/CTEST2", json={"ciudad": "Córdoba"})
    assert r.status_code == 200
    # la modificación devuelve el documento ya actualizado
    body = r.json()
    assert body["ciudad"] == "Córdoba"  # refleja el cambio
    assert body["nombre"] == "Mod"      # conserva el resto de los campos
    assert "_id" not in body

def test_q13_baja_logica(client):
    nuevo = {"id_propietario": "CTEST3", "nombre": "Baja", "apellido": "Test",
             "dni": "77777777", "email": "baja@test.com", "telefono": "1177777777",
             "ciudad": "Salta", "provincia": "Salta"}
    client.post("/propietarios", json=nuevo)

    r = client.delete("/propietarios/CTEST3")
    assert r.status_code == 200
    # la baja lógica devuelve el documento ya marcado como inactivo (no lo borra)
    body = r.json()
    assert body["id_propietario"] == "CTEST3"
    assert body["activo"] is False
    assert "_id" not in body

def test_q13_alta_duplicada_da_409(client):
    # C001 ya existe en el seed; con cuerpo válido debe fallar por duplicado
    r = client.post("/propietarios", json={
        "id_propietario": "C001", "nombre": "Dup", "apellido": "Dup",
        "dni": "30456789", "email": "dup@test.com", "telefono": "1100000000",
        "ciudad": "CABA", "provincia": "Buenos Aires",
    })
    assert r.status_code == 409

def test_q13_alta_incompleta_da_422(client):
    # faltan campos requeridos → validación Pydantic
    r = client.post("/propietarios", json={"id_propietario": "CINCOMPLETO"})
    assert r.status_code == 422

def test_q13_modificar_inexistente_da_404(client):
    # PUT sobre un id que no existe no debe devolver 200 null, sino 404
    r = client.put("/propietarios/CNOEXISTE", json={"ciudad": "Córdoba"})
    assert r.status_code == 404

def test_q13_baja_inexistente_da_404(client):
    r = client.delete("/propietarios/CNOEXISTE")
    assert r.status_code == 404
