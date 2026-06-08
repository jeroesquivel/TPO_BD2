from src.db.cache import get_or_set_cache, cache_key, TTL_DEFAULT
from src.queries import (
    q01_pacientes_activos      as q01,
    q03_historial_paciente     as q03,
    q06_vacunas_vencidas       as q06,
    q10_pacientes_por_sucursal as q10,
)


def get_pacientes_activos():
    return get_or_set_cache(cache_key("q01"), TTL_DEFAULT,
                            q01.pacientes_activos_con_propietario)


def get_historial(id_paciente: str):
    return get_or_set_cache(cache_key("q03", id_paciente), TTL_DEFAULT,
                            lambda: q03.historial_paciente(id_paciente))


def get_vacunas_vencidas():
    return get_or_set_cache(cache_key("q06"), TTL_DEFAULT,
                            lambda: q06.vacunas_vencidas(None))


def get_pacientes_por_sucursal(sucursal: str):
    return get_or_set_cache(cache_key("q10", sucursal), TTL_DEFAULT,
                            lambda: q10.pacientes_por_sucursal(sucursal))
