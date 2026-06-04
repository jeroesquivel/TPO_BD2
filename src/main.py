"""Punto de entrada de VetSalud.

Permite ejecutar el ETL completo y correr las 15 consultas/servicios, ya sea de
forma interactiva (menú) o por línea de comandos.

Uso:
    python -m src.main etl            # ejecuta load_mongo + load_redis + seed_extra
    python -m src.main all            # corre las 15 consultas (ejemplos)
    python -m src.main q07            # corre una consulta puntual
    python -m src.main                # menú interactivo
"""

from __future__ import annotations

import sys

from src.db import mongo, redis_client
from src.loaders import load_mongo, load_redis, seed_extra
from src.queries import (
    q01_pacientes_activos,
    q02_consultas_seguimiento,
    q03_historial_paciente,
    q04_propietarios_multipaciente,
    q05_vets_consultas_60dias,
    q06_vacunas_vencidas,
    q07_top_diagnosticos,
    q08_stock_bajo,
    q09_control_bajo_costo,
    q10_pacientes_por_sucursal,
    q11_ingresos_por_vet_mes,
    q12_propietarios_sin_consultas,
    q13_abm_propietarios,
    q14_registrar_consulta,
    q15_decrementar_stock,
)
from src.queries._util import print_result

# (clave, descripción, callable que devuelve filas para imprimir)
CONSULTAS = {
    "q01": ("Pacientes activos con propietario",
            q01_pacientes_activos.pacientes_activos_con_propietario),
    "q02": ("Consultas en Seguimiento",
            q02_consultas_seguimiento.consultas_en_seguimiento),
    "q03": ("Historial del paciente P001",
            lambda: q03_historial_paciente.historial_paciente("P001")),
    "q04": ("Propietarios con más de un paciente",
            q04_propietarios_multipaciente.propietarios_con_varios_pacientes),
    "q05": ("Vets activos y consultas (60 días)",
            q05_vets_consultas_60dias.vets_activos_consultas_ultimos_60_dias),
    "q06": ("Pacientes con vacunas vencidas",
            q06_vacunas_vencidas.vacunas_vencidas),
    "q07": ("Top 5 diagnósticos",
            q07_top_diagnosticos.top_diagnosticos),
    "q08": ("Stock con menos de 50 unidades",
            q08_stock_bajo.stock_bajo),
    "q09": ("Controles con costo < $5.000",
            q09_control_bajo_costo.consultas_control_bajo_costo),
    "q10": ("Pacientes de la sucursal Palermo",
            lambda: q10_pacientes_por_sucursal.pacientes_por_sucursal("Palermo")),
    "q11": ("Ingresos por veterinario (mes actual)",
            q11_ingresos_por_vet_mes.ingresos_por_vet_mes_actual),
    "q12": ("Propietarios sin consultas en el último año",
            q12_propietarios_sin_consultas.propietarios_sin_consultas_ultimo_anio),
}

# Los servicios mutadores se demuestran con su propio bloque __main__.
SERVICIOS = ("q13", "q14", "q15")


def run_etl() -> None:
    """Ejecuta el pipeline de carga completo (Mongo + Redis + seed)."""
    print(">> Verificando conexiones...")
    mongo.ping()
    redis_client.ping()
    print(">> Cargando MongoDB (base)...")
    load_mongo.load()
    print(">> Cargando Redis (stock base)...")
    load_redis.load()
    print(">> Cargando registros adicionales (seed)...")
    seed_extra.seed()
    print(">> ETL completo.")


def run_consulta(clave: str) -> None:
    titulo, fn = CONSULTAS[clave]
    print_result(f"{clave.upper()} - {titulo}", fn())


def _demo_q13() -> None:
    """Demuestra el ABM de propietarios (alta -> modificación -> baja lógica)."""
    nuevo = {
        "id_propietario": "C999", "nombre": "Demo", "apellido": "Prueba",
        "dni": "99999999", "email": "demo@vetsalud.com", "telefono": "1100000000",
        "ciudad": "CABA", "provincia": "Buenos Aires",
    }
    q13_abm_propietarios.alta_propietario(nuevo)
    print_result("Q13 - Alta", [q13_abm_propietarios.obtener_propietario("C999")])
    q13_abm_propietarios.modificar_propietario(
        "C999", {"email": "demo.nuevo@vetsalud.com", "telefono": "1122223333"})
    print_result("Q13 - Modificación",
                 [q13_abm_propietarios.obtener_propietario("C999")])
    q13_abm_propietarios.baja_logica_propietario("C999")
    print_result("Q13 - Baja lógica",
                 [q13_abm_propietarios.obtener_propietario("C999")])


def _demo_q14() -> None:
    """Demuestra el registro de una consulta y la validación de inexistentes."""
    nueva = q14_registrar_consulta.registrar_consulta(
        "P001", "V001", "Control de rutina", "Sano", 4300, estado="Cerrada")
    print_result("Q14 - Nueva consulta registrada", [nueva])
    try:
        q14_registrar_consulta.registrar_consulta("P999", "V001", "x", "y", 100)
    except q14_registrar_consulta.ValidacionError as exc:
        print(f"Validación OK -> {exc}")


def _demo_q15() -> None:
    """Demuestra el decremento de stock y el control de stock insuficiente."""
    print_result("Q15 - Decremento de stock",
                 [q15_decrementar_stock.decrementar_stock("PRD001", 5)])
    try:
        q15_decrementar_stock.decrementar_stock("PRD006", 10_000)
    except q15_decrementar_stock.StockError as exc:
        print(f"Validación OK -> {exc}")


def run_servicio(clave: str) -> None:
    """Ejecuta el bloque demostrativo de un servicio mutador."""
    print(f"\n### Servicio {clave.upper()} ###")
    {"q13": _demo_q13, "q14": _demo_q14, "q15": _demo_q15}[clave]()


def run_all() -> None:
    for clave in CONSULTAS:
        run_consulta(clave)
    for clave in SERVICIOS:
        run_servicio(clave)


def menu() -> None:  # pragma: no cover
    opciones = list(CONSULTAS.items())
    while True:
        print("\n==== VetSalud — Menú ====")
        print(" 0) Ejecutar ETL completo (carga de datos)")
        for clave, (titulo, _) in opciones:
            print(f" {clave}) {titulo}")
        for clave in SERVICIOS:
            print(f" {clave}) Servicio mutador {clave.upper()}")
        print(" all) Ejecutar todas las consultas")
        print(" q) Salir")
        eleccion = input("Opción: ").strip().lower()
        if eleccion in ("q", "salir", "exit"):
            break
        if eleccion == "0":
            run_etl()
        elif eleccion == "all":
            run_all()
        elif eleccion in CONSULTAS:
            run_consulta(eleccion)
        elif eleccion in SERVICIOS:
            run_servicio(eleccion)
        else:
            print("Opción no válida.")


def main(argv: list[str]) -> None:
    if not argv:
        menu()
        return
    comando = argv[0].lower()
    if comando == "etl":
        run_etl()
    elif comando == "all":
        run_all()
    elif comando in CONSULTAS:
        run_consulta(comando)
    elif comando in SERVICIOS:
        run_servicio(comando)
    else:
        print(f"Comando desconocido: {comando}")
        print(__doc__)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:])
