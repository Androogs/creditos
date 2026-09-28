from backend.services.motor_parametros import MotorParametros
from backend.services.reglas_filtros_duros import (
    DatosBuroParaFiltros,
    evaluar_filtros_duros,
)


def _params() -> MotorParametros:
    return MotorParametros()


def test_cliente_limpio_sin_causales():
    datos = DatosBuroParaFiltros(edad=30)
    causales = evaluar_filtros_duros(datos, _params())
    assert causales == []


def test_edad_fuera_de_rango_18_65():
    datos = DatosBuroParaFiltros(edad=17)
    causales = evaluar_filtros_duros(datos, _params())
    codigos = [c.codigo for c in causales]
    assert "POL_EDAD" in codigos

    datos2 = DatosBuroParaFiltros(edad=66)
    causales2 = evaluar_filtros_duros(datos2, _params())
    assert "POL_EDAD" in [c.codigo for c in causales2]


def test_edad_en_el_limite_no_dispara():
    datos = DatosBuroParaFiltros(edad=18)
    causales = evaluar_filtros_duros(datos, _params())
    assert causales == []

    datos2 = DatosBuroParaFiltros(edad=65)
    causales2 = evaluar_filtros_duros(datos2, _params())
    assert causales2 == []


def test_nacionalidad_no_colombiana_dispara():
    datos = DatosBuroParaFiltros(edad=30, nacionalidad_colombiana=False)
    causales = evaluar_filtros_duros(datos, _params())
    assert "POL_NACIONALIDAD" in [c.codigo for c in causales]


def test_multas_runt_dispara():
    datos = DatosBuroParaFiltros(edad=30, tiene_multas_runt=True)
    causales = evaluar_filtros_duros(datos, _params())
    assert "POL_RUNT" in [c.codigo for c in causales]


def test_mora_30_historica_umbral_2_no_4():
    # El BRD real dice >= 2, no >= 4 como el resumen anterior.
    datos = DatosBuroParaFiltros(edad=30, mora_30_historica_veces=1)
    causales = evaluar_filtros_duros(datos, _params())
    assert causales == []

    datos2 = DatosBuroParaFiltros(edad=30, mora_30_historica_veces=2)
    causales2 = evaluar_filtros_duros(datos2, _params())
    assert "POL6" in [c.codigo for c in causales2]


def test_documento_no_vigente_dispara_salvo_cedula_extranjeria():
    datos = DatosBuroParaFiltros(edad=30, documento_vigente=False)
    causales = evaluar_filtros_duros(datos, _params())
    assert "POL11" in [c.codigo for c in causales]

    datos2 = DatosBuroParaFiltros(
        edad=30,
        documento_vigente=False,
        documento_es_cedula_extranjeria=True,
    )
    causales2 = evaluar_filtros_duros(datos2, _params())
    assert "POL11" not in [c.codigo for c in causales2]


def test_mora_30_vigente_dispara_rechazo():
    # En el BRD real esto ya es Rechazo (antes era Estudio).
    datos = DatosBuroParaFiltros(edad=30, mora_30_vigente=True)
    causales = evaluar_filtros_duros(datos, _params())
    assert "MORA30_VIGENTE" in [c.codigo for c in causales]


def test_exclusion_persona_no_natural():
    datos = DatosBuroParaFiltros(edad=30, es_persona_natural=False)
    causales = evaluar_filtros_duros(datos, _params())
    assert "EXCL_PJ" in [c.codigo for c in causales]


def test_exclusion_fallecido():
    datos = DatosBuroParaFiltros(edad=30, reportado_fallecido=True)
    causales = evaluar_filtros_duros(datos, _params())
    assert "EXCL_FALLECIDO" in [c.codigo for c in causales]


def test_calificacion_k_dispara():
    datos = DatosBuroParaFiltros(edad=30, calificacion="K")
    causales = evaluar_filtros_duros(datos, _params())
    assert "POL9" in [c.codigo for c in causales]
