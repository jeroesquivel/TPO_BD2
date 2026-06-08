from src.db.cache import get_or_set_cache, invalidate, cache_key, TTL_DEFAULT, TTL_LARGO
from src.queries import (
    q02_consultas_seguimiento  as q02,
    q05_vets_consultas_60dias  as q05,
    q07_top_diagnosticos       as q07,
    q09_control_bajo_costo     as q09,
    q11_ingresos_por_vet_mes   as q11,
    q14_registrar_consulta     as q14,
)


def get_consultas_seguimiento():
    return get_or_set_cache(cache_key("q02"), TTL_DEFAULT,
                            q02.consultas_en_seguimiento)


def get_vets_activos():
    # None → datetime.now() en tiempo real
    return get_or_set_cache(cache_key("q05"), TTL_DEFAULT,
                            lambda: q05.vets_activos_consultas_ultimos_60_dias(None))


def get_top_diagnosticos(limite: int = 5):
    return get_or_set_cache(cache_key("q07", limite), TTL_LARGO,
                            lambda: q07.top_diagnosticos(limite))


def get_control_bajo_costo(umbral: float = 5000):
    return get_or_set_cache(cache_key("q09", umbral), TTL_DEFAULT,
                            lambda: q09.consultas_control_bajo_costo(umbral))


def get_ingresos_por_vet():
    # None → datetime.now() en tiempo real
    return get_or_set_cache(cache_key("q11"), TTL_DEFAULT,
                            lambda: q11.ingresos_por_vet_mes_actual(None))


def registrar_consulta(data: dict):
    out = q14.registrar_consulta(**data)
    # Una nueva consulta puede afectar: historial (q03), actividad del vet (q05),
    # diagnósticos (q07), controles (q09), pacientes por sucursal (q10),
    # ingresos (q11), propietarios sin consultas (q12), seguimiento (q02).
    invalidate("q02", "q03", "q05", "q07", "q09", "q10", "q11", "q12")
    return out
