from src.db.cache import get_or_set_cache, invalidate, cache_key, TTL_DEFAULT
from src.queries import (
    q04_propietarios_multipaciente  as q04,
    q12_propietarios_sin_consultas  as q12,
    q13_abm_propietarios            as q13,
)


def get_propietarios_multipaciente():
    return get_or_set_cache(cache_key("q04"), TTL_DEFAULT,
                            q04.propietarios_con_varios_pacientes)


def get_propietarios_sin_consultas():
    return get_or_set_cache(cache_key("q12"), TTL_DEFAULT,
                            lambda: q12.propietarios_sin_consultas_ultimo_anio(None))


def _invalidar_propietarios():
    invalidate("q01", "q04", "q12")


def alta_propietario(data: dict):
    out = q13.alta_propietario(data)
    _invalidar_propietarios()
    return out


def modificar_propietario(id_p: str, cambios: dict):
    out = q13.modificar_propietario(id_p, cambios)
    _invalidar_propietarios()
    return out


def baja_propietario(id_p: str):
    out = q13.baja_logica_propietario(id_p)
    _invalidar_propietarios()
    return out
