import pytest

from backend.services.finanzas import (
    cuota_a_valor_mensual,
    cuota_anualidad,
    valor_presente_anualidad,
)


def test_cuota_anualidad_corrige_el_bug_del_excel():
    # El Excel de referencia (con el error de paréntesis) daba 19.5
    # para estos valores; el correcto es ~39.23.
    cuota = cuota_anualidad(monto=1000, tasa_pct=2.0, plazo_meses=36)
    assert cuota == pytest.approx(39.23, abs=0.01)


def test_cuota_anualidad_segundo_caso_del_excel():
    # El Excel daba 2063.74; el correcto es ~2770.57.
    cuota = cuota_anualidad(monto=103200, tasa_pct=2.0, plazo_meses=69)
    assert cuota == pytest.approx(2770.57, abs=0.01)


def test_valor_presente_es_la_inversa_de_cuota_anualidad():
    monto = 5_000_000
    tasa = 1.8
    plazo = 24

    cuota = cuota_anualidad(monto, tasa, plazo)
    monto_recuperado = valor_presente_anualidad(cuota, tasa, plazo)

    assert monto_recuperado == pytest.approx(monto, rel=1e-6)


def test_cuota_a_valor_mensual_periodicidades():
    assert cuota_a_valor_mensual(1200, "bimensual") == 600
    assert cuota_a_valor_mensual(1200, "trimestral") == 400
    assert cuota_a_valor_mensual(1200, "semestral") == 200
    assert cuota_a_valor_mensual(1200, "anual") == 100
    assert cuota_a_valor_mensual(1200, "mensual") == 1200


def test_cuota_a_valor_mensual_periodicidad_invalida():
    with pytest.raises(ValueError):
        cuota_a_valor_mensual(1200, "quincenal")
