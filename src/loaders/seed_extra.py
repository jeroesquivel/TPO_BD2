"""Registros adicionales de poblamiento 

Agrega **al menos 10 registros propios por colección**, diseñados "de atrás hacia
adelante" para que cada una de las 15 consultas devuelva resultados significativos.
La fecha de referencia del proyecto es **2026-06-01**; por eso se incluyen:

- Consultas en los últimos 60 días (2026-04-02 .. 2026-06-01)  -> consulta 5.
- Consultas en el mes actual (2026-06)                          -> consulta 11.
- Vacunaciones con `proxima_dosis` anterior a hoy              -> consulta 6.
- Un propietario cuya última consulta es anterior a 2025-06-01,
  y otros sin consultas                                        -> consulta 12.
- Diagnósticos repetidos                                       -> consulta 7 (Top 5).
- Consultas de motivo "Control" con costo < 5000              -> consulta 9.
- Varias consultas en estado "Seguimiento"                    -> consulta 2.
- Propietarios/pacientes/veterinarios con `activo=false`      -> consulta 13 (baja lógica).
- Stock con unidades < 50 y otros con más                     -> consulta 8.
- Cirugías pobladas desde cero, coherentes con pacientes/vets.

Es idempotente: usa `replace_one(..., upsert=True)` por id natural en MongoDB,
de modo que puede re-ejecutarse sin duplicar.
"""

from __future__ import annotations

from datetime import datetime

from src.db.mongo import get_db


def _d(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d")


PROPIETARIOS = [
    # id, nombre, apellido, dni, email, telefono, ciudad, provincia, activo
    ("C007", "Lucía", "Fernández", "39111222", "lucia@gmail.com", "1145110011", "Buenos Aires", "Buenos Aires", True),
    ("C008", "Martín", "Gómez", "33444555", "martin@gmail.com", "1145220022", "Avellaneda", "Buenos Aires", True),
    ("C009", "Sofía", "Romero", "40555666", "sofia@gmail.com", "1145330033", "Rosario", "Santa Fe", False),
    ("C010", "Javier", "Núñez", "31666777", "javier@gmail.com", "1145440044", "Córdoba", "Córdoba", True),
    ("C011", "Carla", "Benítez", "37777888", "carla@gmail.com", "1145550055", "Mendoza", "Mendoza", True),
    ("C012", "Pedro", "Ledesma", "29888999", "pedro@gmail.com", "1145660066", "Salta", "Salta", True),
    ("C013", "Florencia", "Vega", "42999000", "florencia@gmail.com", "1145770077", "La Plata", "Buenos Aires", True),
    ("C014", "Andrés", "Pereyra", "34000111", "andres@gmail.com", "1145880088", "San Juan", "San Juan", True),
    ("C015", "Mariana", "Acosta", "41222333", "mariana@gmail.com", "1145990099", "Neuquén", "Neuquén", False),
    ("C016", "Gonzalo", "Silva", "32333444", "gonzalo@gmail.com", "1146000100", "Mar del Plata", "Buenos Aires", True),
    ("C017", "Rocío", "Cabrera", "38444555", "rocio@gmail.com", "1146110111", "Tucumán", "Tucumán", True),
    ("C018", "Esteban", "Ortiz", "30555666", "esteban@gmail.com", "1146220122", "Bahía Blanca", "Buenos Aires", True),
]

PACIENTES = [
    # id, nombre, especie, raza, fecha_nac, id_propietario, activo
    ("P009", "Toby", "Perro", "Golden Retriever", "2020-03-10", "C007", True),
    ("P010", "Mishi", "Gato", "Atigrado", "2022-05-22", "C007", True),
    ("P011", "Rocky", "Perro", "Bulldog", "2019-08-30", "C008", True),
    ("P012", "Copito", "Conejo", "Mini Lop", "2023-04-18", "C010", True),
    ("P013", "Tango", "Perro", "Border Collie", "2016-12-01", "C011", True),
    ("P014", "Pelusa", "Gato", "Común Europeo", "2021-09-09", "C013", False),
    ("P015", "Zeus", "Perro", "Rottweiler", "2018-02-25", "C014", True),
    ("P016", "Nala", "Gato", "Maine Coon", "2022-11-11", "C016", True),
    ("P017", "Simba", "Perro", "Boxer", "2019-06-15", "C017", True),
    ("P018", "Kira", "Perro", "Dálmata", "2021-01-20", "C017", True),
    ("P019", "Lola", "Gato", "Sphynx", "2023-07-07", "C018", True),
    ("P020", "Manchas", "Perro", "Cocker", "2017-10-05", "C015", False),
]

VETERINARIOS = [
    # id, nombre, apellido, matricula, especialidad, sucursal, activo
    ("V006", "Diego", "Morales", "VET-0120", "Clínica General", "Núñez", True),
    ("V007", "Sabrina", "Luna", "VET-0133", "Cirugía", "Flores", True),
    ("V008", "Federico", "Paz", "VET-0145", "Dermatología", "Quilmes", True),
    ("V009", "Natalia", "Vera", "VET-0150", "Cardiología", "Belgrano", True),
    ("V010", "Ramiro", "Sosa", "VET-0161", "Oftalmología", "Tigre", False),
    ("V011", "Julieta", "Campos", "VET-0172", "Odontología", "Palermo", True),
    ("V012", "Nicolás", "Bravo", "VET-0184", "Traumatología", "Caballito", True),
    ("V013", "Carolina", "Méndez", "VET-0190", "Clínica General", "Morón", True),
    ("V014", "Tomás", "Figueroa", "VET-0205", "Oncología", "La Plata", True),
    ("V015", "Belén", "Ríos", "VET-0211", "Clínica General", "Devoto", True),
    ("V016", "Ignacio", "Herrera", "VET-0223", "Nutrición", "Palermo", True),
]

CONSULTAS = [
    # id, id_paciente, id_vet, fecha, motivo, diagnostico, costo, estado
    ("CON009", "P005", "V005", "2026-04-10", "Vómitos", "Gastritis", 5200, "Seguimiento"),
    ("CON010", "P002", "V003", "2026-04-15", "Alergia cutánea", "Dermatitis atópica", 6400, "Seguimiento"),
    ("CON011", "P009", "V006", "2026-04-20", "Control", "Sano", 3500, "Cerrada"),
    ("CON012", "P010", "V006", "2026-05-02", "Otitis", "Otitis externa", 4800, "Cerrada"),
    ("CON013", "P011", "V007", "2026-05-05", "Control", "Sano", 2800, "Cerrada"),
    ("CON014", "P006", "V003", "2026-05-10", "Picazón persistente", "Dermatitis atópica", 5900, "Seguimiento"),
    ("CON015", "P015", "V012", "2026-05-12", "Cojera", "Esguince", 7000, "Cerrada"),
    ("CON016", "P016", "V013", "2026-05-15", "Vómitos", "Gastritis", 4900, "Seguimiento"),
    ("CON017", "P017", "V008", "2026-05-18", "Otitis", "Otitis externa", 5100, "Cerrada"),
    ("CON018", "P018", "V008", "2026-05-20", "Desparasitación", "Parásitos intestinales", 3200, "Cerrada"),
    ("CON019", "P019", "V015", "2026-05-22", "Control", "Sano", 4200, "Cerrada"),
    ("CON020", "P005", "V005", "2026-05-25", "Seguimiento gastritis", "Gastritis", 3000, "Seguimiento"),
    ("CON021", "P010", "V006", "2026-05-28", "Otitis", "Otitis externa", 4600, "Cerrada"),
    ("CON022", "P002", "V003", "2026-06-01", "Control dermatitis", "Dermatitis atópica", 6800, "Seguimiento"),
    ("CON023", "P009", "V006", "2026-06-01", "Vómitos", "Gastritis", 5300, "Cerrada"),
    ("CON024", "P016", "V013", "2026-06-01", "Desparasitación", "Parásitos intestinales", 3400, "Cerrada"),
    ("CON025", "P001", "V001", "2026-06-01", "Control anual", "Sano", 4000, "Cerrada"),
    # Consulta antigua de P013 (propietario C011): su última consulta queda
    # ANTES de 2025-06-01, por lo que C011 aparece en la consulta 12.
    ("CON026", "P013", "V001", "2024-12-10", "Control anual", "Sano", 3000, "Cerrada"),
    # Consultas de junio 2026 días 02-05: concentradas en V003/V006/V001
    # para que q11 muestre acumulación real en el mes.
    ("CON027", "P002", "V003", "2026-06-02", "Revisión dermatitis", "Dermatitis atópica", 6200, "Seguimiento"),
    ("CON028", "P009", "V006", "2026-06-03", "Control post-cirugía", "Sano", 3800, "Cerrada"),
    ("CON029", "P010", "V006", "2026-06-03", "Otitis", "Otitis externa", 4700, "Cerrada"),
    ("CON030", "P001", "V001", "2026-06-04", "Vacunación anual", "Sano", 4100, "Cerrada"),
    ("CON031", "P016", "V003", "2026-06-05", "Seguimiento alergia", "Dermatitis atópica", 5800, "Seguimiento"),
]

VACUNACIONES = [
    # id, id_paciente, id_vet, fecha_aplicacion, nombre_vacuna, proxima_dosis
    ("VAC007", "P012", "V006", "2025-05-01", "Antirrábica", "2026-05-01"),  # vencida
    ("VAC008", "P009", "V006", "2025-04-10", "Sextuple", "2026-04-10"),     # vencida
    ("VAC009", "P010", "V006", "2025-03-15", "Triple Felina", "2026-03-15"),  # vencida
    ("VAC010", "P002", "V003", "2025-05-20", "Antirrábica", "2026-05-20"),  # vencida
    ("VAC011", "P016", "V013", "2026-01-10", "Sextuple", "2027-01-10"),     # futura
    ("VAC012", "P017", "V008", "2026-02-12", "Antirrábica", "2027-02-12"),  # futura
    ("VAC013", "P019", "V015", "2026-03-01", "Triple Felina", "2027-03-01"),  # futura
    ("VAC014", "P005", "V005", "2025-12-01", "Sextuple", "2026-12-01"),     # futura
    ("VAC015", "P011", "V007", "2025-05-25", "Antirrábica", "2026-05-25"),  # vencida
    ("VAC016", "P015", "V012", "2026-04-01", "Antirrábica", "2027-04-01"),  # futura
    ("VAC017", "P012", "V006", "2026-04-15", "Sextuple", "2027-04-15"),     # futura
    ("VAC018", "P017", "V008", "2026-05-10", "Triple Felina", "2027-05-10"),  # futura
    ("VAC019", "P002", "V003", "2025-03-12", "Sextuple", "2026-03-12"),     # vencida
]

CIRUGIAS = [
    # id, id_paciente, id_vet, fecha, tipo, resultado, costo
    ("CIR001", "P003", "V002", "2025-09-21", "Osteosíntesis", "Exitosa", 25000),
    ("CIR002", "P007", "V002", "2025-12-11", "Extracción dentaria múltiple", "Exitosa", 18000),
    ("CIR003", "P005", "V007", "2026-04-12", "Gastrotomía", "Exitosa", 32000),
    ("CIR004", "P015", "V012", "2026-05-13", "Reducción de fractura", "Exitosa", 28000),
    ("CIR005", "P001", "V002", "2026-05-20", "Extirpación de tumor", "Exitosa", 35000),
    ("CIR006", "P016", "V007", "2026-05-25", "Esterilización", "Exitosa", 15000),
    ("CIR007", "P002", "V002", "2026-06-01", "Biopsia cutánea", "Pendiente de resultado", 12000),
    ("CIR008", "P010", "V012", "2026-03-30", "Limpieza dental", "Exitosa", 9000),
    ("CIR009", "P009", "V007", "2026-02-15", "Esterilización", "Exitosa", 15000),
    ("CIR010", "P017", "V002", "2026-01-20", "Reparación de hernia", "Exitosa", 22000),
    ("CIR011", "P019", "V012", "2026-05-29", "Esterilización", "Exitosa", 16000),
]

# Stock adicional en Redis: mezcla de productos con unidades < 50 (consulta 8)
# y con más, y algunos con vencimiento cercano.
STOCK = [
    # id_producto, nombre, categoria, unidades, precio_unit, vencimiento, proveedor
    ("PRD007", "Amoxicilina 500mg",  "Antibiótico",      95,  1200, "2026-08-15", "VetFarma SA"),
    ("PRD008", "Dexametasona 4mg",   "Antiinflamatorio", 70,  980,  "2026-07-20", "BioVet SRL"),
    ("PRD009", "Tramadol 50mg",      "Analgésico",       45,  2100, "2027-01-05", "MediAnimal"),
    ("PRD010", "Metronidazol 250mg", "Antibiótico",      110, 750,  "2026-09-30", "VetFarma SA"),
    ("PRD011", "Prednisolona 5mg",   "Corticoide",       30,  1350, "2026-06-25", "BioVet SRL"),
    ("PRD012", "Enrofloxacina 50mg", "Antibiótico",      80,  1600, "2027-03-10", "MediAnimal"),
    ("PRD013", "Suero glucosado 5%", "Solución",         150, 350,  "2026-11-01", "VetFarma SA"),
    ("PRD014", "Vitamina B12 inj.",  "Suplemento",       40,  890,  "2026-10-20", "BioVet SRL"),
    ("PRD015", "Omeprazol 20mg",     "Gastroprotector",  60,  1100, "2027-02-28", "MediAnimal"),
    ("PRD016", "Furosemida 40mg",    "Diurético",        20,  1450, "2026-07-15", "VetFarma SA"),
]


def _upsert(coll, key: str, docs: list[dict]) -> int:
    for doc in docs:
        coll.replace_one({key: doc[key]}, doc, upsert=True)
    return len(docs)


def seed() -> dict[str, int]:
    """Inserta los registros adicionales en MongoDB. Idempotente."""
    db = get_db()

    propietarios = [
        dict(zip(
            ("id_propietario", "nombre", "apellido", "dni", "email",
             "telefono", "ciudad", "provincia", "activo"), row))
        for row in PROPIETARIOS
    ]
    pacientes = [
        {
            "id_paciente": p[0], "nombre": p[1], "especie": p[2], "raza": p[3],
            "fecha_nac": _d(p[4]), "id_propietario": p[5], "activo": p[6],
        }
        for p in PACIENTES
    ]
    veterinarios = [
        dict(zip(
            ("id_vet", "nombre", "apellido", "matricula",
             "especialidad", "sucursal", "activo"), row))
        for row in VETERINARIOS
    ]

    counts: dict[str, int] = {}
    counts["propietarios"] = _upsert(db.propietarios, "id_propietario", propietarios)
    counts["veterinarios"] = _upsert(db.veterinarios, "id_vet", veterinarios)
    counts["pacientes"] = _upsert(db.pacientes, "id_paciente", pacientes)

    # Lookup dicts completos (CSV base + seed) para resolver snapshots
    vet_by_id = {v["id_vet"]: v for v in db.veterinarios.find({}, {"_id": 0})}
    pac_by_id = {p["id_paciente"]: p for p in db.pacientes.find({}, {"_id": 0})}

    consultas = [
        {
            "id_consulta": c[0], "id_paciente": c[1], "id_vet": c[2],
            "fecha": _d(c[3]), "motivo": c[4], "diagnostico": c[5],
            "costo": c[6], "estado": c[7],
            "vet_nombre":      vet_by_id[c[2]]["nombre"],
            "vet_apellido":    vet_by_id[c[2]]["apellido"],
            "vet_especialidad": vet_by_id[c[2]]["especialidad"],
            "vet_sucursal":    vet_by_id[c[2]]["sucursal"],
            "id_propietario":  pac_by_id[c[1]]["id_propietario"],
        }
        for c in CONSULTAS
    ]
    vacunaciones = [
        {
            "id_vacuna": v[0], "id_paciente": v[1], "id_vet": v[2],
            "fecha_aplicacion": _d(v[3]), "nombre_vacuna": v[4],
            "proxima_dosis": _d(v[5]),
            "vet_nombre":      vet_by_id[v[2]]["nombre"],
            "vet_apellido":    vet_by_id[v[2]]["apellido"],
            "vet_especialidad": vet_by_id[v[2]]["especialidad"],
            "vet_sucursal":    vet_by_id[v[2]]["sucursal"],
        }
        for v in VACUNACIONES
    ]
    cirugias = [
        {
            "id_cirugia": c[0], "id_paciente": c[1], "id_vet": c[2],
            "fecha": _d(c[3]), "tipo": c[4], "resultado": c[5], "costo": c[6],
        }
        for c in CIRUGIAS
    ]

    counts["consultas"] = _upsert(db.consultas, "id_consulta", consultas)
    counts["vacunaciones"] = _upsert(db.vacunaciones, "id_vacuna", vacunaciones)
    counts["cirugias"] = _upsert(db.cirugias, "id_cirugia", cirugias)

    productos = [
        {
            "id_producto": s[0], "nombre": s[1], "categoria": s[2],
            "unidades": s[3], "precio_unit": s[4],
            "vencimiento": _d(s[5]), "proveedor": s[6],
        }
        for s in STOCK
    ]
    counts["stock"] = _upsert(db.stock, "id_producto", productos)

    return counts


if __name__ == "__main__":  # pragma: no cover
    result = seed()
    print("Registros adicionales cargados:")
    for coll, n in result.items():
        print(f"  - {coll}: +{n}")
