import pytest

from backend.services.reglas_ingreso import calcular_ingreso_final


def test_empleado_usa_valor_ingreso():
    r = calcular_ingreso_final(
        "Empleado", valor_ingreso=2_000_000, quanto3_medo=0,
        ingresos_mensuales_declarados=1_000_000,
    )
    assert r.ingreso_final == 2_000_000
    assert r.rechazado is False


def test_empleado_sin_valor_ingreso_rechaza_no_cae_a_declaradso():
    # Diferencia clave vs. la primera versión: No hay fallback a
    # ingreso declarado para Empleado/Pensionado.
    r = calcular_ingreso_final(
        "Empleado", valor_ingreso=0, quanto3_medio=0,
        ingresos_mensuales_declarados=1_000_000,
    )
    assert r.rechazado is True
    assert r.causal_codigo == "SIN_VALOR_INGRESO_Y_QUANTO"


def test_independiente_usa_quanto():
    r = calcular_ingreso_final(
        "Independiente", valor_ingreso=5_000_000, quanto3_medio=2_000_000,
        ingresos_mensuales_declarados=1_000_000,
    )
    assert r.ingreso_final == 2_000_000
    assert r.fuente_usada == "quanto3_medio"


def test_independiente_sin_quanto_rechaza():
    r = calcular_ingreso_final(
        "Independiente", valor_ingreso=0, quanto3_medio=0,
        ingresos_mensuales_declarados=1_000_000
    )
    assert r.rechazado is True


def test_fuerzas_militares_cae_a_quanto_si_no_hay_valor_ingreso():
    r = calcular_ingreso_final(
        "Fuerzas Militares", valor_ingreso=0, quanto3_medio=1_500_000,
        ingresos_mensuales_declarados=1_000_000,
    )
    assert r.ingreso_final == 1_500_000
    assert r.fuente_usada == "quanto3_medio"


def test_ocupacion_no_reconocida():
    with pytest.raises(ValueError):
        calcular_ingreso_final(
            "Estudiante", valor_ingreso=1, quanto3_medio=1,
            ingresos_mensuales_declarados=1,
        )
