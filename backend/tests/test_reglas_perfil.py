from backend.services.motor_parametros import MotorParametros
from backend.services.reglas_perfil import (
    decidir_por_ocupacion,
    perfil_ingreso_empleado,
    perfil_ingreso_independiente,
    perfil_ingreso_pensionado_ffmm,
    perfil_score_empleado_pensionado_ffmm,
    perfil_score_independiente,
)


def _params() -> MotorParametros:
    return MotorParametros()  # ya trae los valores reales del BRD


# --- Perfil de score ---

def test_score_empleado_a():
    assert perfil_score_empleado_pensionado_ffmm(760, _params()) == "A"


def test_score_empleado_b():
    assert perfil_score_empleado_pensionado_ffmm(700, _params()) == "B"


def test_score_empleado_c():
    assert perfil_score_empleado_pensionado_ffmm(620, _params()) == "C"


def test_score_empleado_d():
    assert perfil_score_empleado_pensionado_ffmm(550, _params()) == "D"


def test_score_empleado_rechazo_punto_corte():
    assert (
        perfil_score_empleado_pensionado_ffmm(300, _params())
        == "RECHAZO_PUNTO_CORTE"
    )


def test_score_empleado_rechazo_sin_experiencia():
    assert (
        perfil_score_empleado_pensionado_ffmm(100, _params())
        == "RECHAZO_SIN_EXPERIENCIA"
    )


def test_score_independiente_a():
    assert perfil_score_independiente(800, _params()) == "A"


def test_score_independiente_d():
    assert perfil_score_independiente(550, _params()) == "D"


# --- Perfil de ingreso: Empleado ---

def test_ingreso_empleado_alto_indefinido():
    resultado = perfil_ingreso_empleado(
        ingreso_final_smmlv=2.0,
        tipo_contrato="Indefinido",
        meses_continuidad=6,
        params=_params(),
    )
    assert resultado == "ALTO"


def test_ingreso_empleado_gris_sin_continuidad():
    resultado = perfil_ingreso_empleado(
        ingreso_final_smmlv=2.0,
        tipo_contrato="Indefinido",
        meses_continuidad=2,  # < 5
        params=_params(),
    )
    assert resultado == "GRIS"


def test_ingreso_empleado_bajo():
    resultado = perfil_ingreso_empleado(
        ingreso_final_smmlv=1.1,
        tipo_contrato="Indefinido",
        meses_continuidad=6,
        params=_params(),
    )
    assert resultado == "BAJO"


def test_ingreso_empleado_rechazo():
    resultado = perfil_ingreso_empleado(
        ingreso_final_smmlv=0.9,
        tipo_contrato="Indefinido",
        meses_continuidad=6,
        params=_params(),
    )
    assert resultado == "RECHAZO"


def test_ingreso_empleado_fijo_requiere_10_meses():
    resultado = perfil_ingreso_empleado(
        ingreso_final_smmlv=2.0,
        tipo_contrato="Fijo",
        meses_continuidad=9,  # < 10
        params=_params(),
    )
    assert resultado == "GRIS"

    resultado_ok = perfil_ingreso_empleado(
        ingreso_final_smmlv=2.0,
        tipo_contrato="Fijo",
        meses_continuidad=10,
        params=_params(),
    )
    assert resultado_ok == "ALTO"


# --- Perfil de ingreso: Pensionado / Fuerzas Militares ---

def test_ingreso_pensionado_alto():
    assert perfil_ingreso_pensionado_ffmm(1.8, _params()) == "ALTO"


def test_ingreso_pensionado_rechazo():
    assert perfil_ingreso_pensionado_ffmm(0.5, _params()) == "RECHAZO"


# --- Perfil de ingreso: Independiente ---

def test_ingreso_independiente_alto():
    resultado = perfil_ingreso_independiente(2.6, 2, _params())
    assert resultado == "ALTO"


def test_ingreso_independiente_rechazo():
    resultado = perfil_ingreso_independiente(1.0, 5, _params())
    assert resultado == "RECHAZO"


# --- Matriz de decisión ---

def test_matriz_empleado_bajo_es_aprobado():
    resultado = decidir_por_ocupacion("Empleado", "C", "BAJO")
    assert resultado.decision == "APROBADO"


def test_matriz_empleado_gris_es_rechazado():
    resultado = decidir_por_ocupacion("Empleado", "A", "GRIS")
    assert resultado.decision == "RECHAZADO"
    assert resultado.causal_codigo == "GRIS_NO_CONTINUIDAD"


def test_matriz_empleado_score_d_es_rechazado():
    resultado = decidir_por_ocupacion("Empleado", "D", "ALTO")
    assert resultado.decision == "RECHAZADO"
    assert resultado.causal_codigo == "D_NO_CUMPLE_SCORE"


def test_matriz_pensionado_bajo_es_rechazado():
    # Distinto de Empleado: para Pensionado, BAJO SÍ rechaza.
    resultado = decidir_por_ocupacion("Pensionado", "A", "BAJO")
    assert resultado.decision == "RECHAZADO"
    assert resultado.causal_codigo == "BAJO_NO_INGRESOS"


def test_matriz_independiente_gris_causal_camara():
    resultado = decidir_por_ocupacion("Independiente", "B", "GRIS")
    assert resultado.decision == "RECHAZADO"
    assert resultado.causal_codigo == "GRIS_NO_CAMARA"


def test_matriz_independiente_alto_es_aprobado():
    resultado = decidir_por_ocupacion("Independiente", "A", "ALTO")
    assert resultado.decision == "APROBADO"
