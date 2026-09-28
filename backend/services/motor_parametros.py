"""
Parámetros de negocio del motor de decisión propio, extraídos del
BRD ORIGINAL (no de un resumen): BRD-Prefiltro_Cliente_
InversionesPacifico_22012026.docx, actualizado 9 septiembre 2026.

A diferencia de la primera versión de este archivo, estos YA SON
los valores reales confirmados en el documento — no placeholders
pendientes de Parametros_IP. Se dejan como dataclass con default
para que sean fáciles de ubicar y de ajustar si el BRD cambia de
versión otra vez, y overrideables por variable de entorno
(MOTOR_<CAMPO>) para no tener que tocar código ante un ajuste.

Únicos campos que siguen sin valor confirmado: los relacionados con
Telcos (Saldo_Mora_BE) — el BRD dice "Para Telcos validar saldo en
mora > Saldo_Mora_BE pesos" pero no da el número, y no hay ninguna
tabla de líneas de telco en el esquema todavía. Se deja en None y
esa regla no se implementa (ver reglas_filtros_duros.py).
"""

import os
from dataclasses import dataclass, fields

_ENV_PREFIX = "MOTOR_"


@dataclass
class MotorParametros:
    # --- Perfil de SCORE (Advance Score) ---
    # Empleado / Pensionado / Fuerzas Militares (BRD sección 2.4.5)
    score_ep_1: float = 750  # >= -> A
    score_ep_2: float = 680  # >= -> B
    score_ep_3: float = 600  # >= -> C
    score_ep_4: float = 500  # >= -> D
    # Independiente / Fuerzas Militares (usa esta escalera para score)
    score_if_1: float = 770
    score_if_2: float = 700
    score_if_3: float = 620
    score_if_4: float = 520
    # Piso común a ambas escaleras: 150 <= score < score_4 ->
    # Rechazado "Score por debajo del punto de corte";
    # score < 150 -> Rechazado "Cliente sin experiencia crediticia".
    score_piso_experiencia: float = 150

    # --- Perfil de INGRESO (en SMMLV) ---
    # Empleado (BRD sección 2.4.6)
    ingreso_e_alto: float = 1.6
    ingreso_e_medio: float = 1.4
    ingreso_e_bajo: float = 1.0
    # continuidad requerida (misma para Alto/Medio/Bajo; si no se
    # cumple con ingreso >= 1.0, degrada a GRIS)
    meses_continuidad_indefinido: int = 5
    meses_continuidad_fijo_o_labor: int = 10

    # Pensionado / Fuerzas Militares (sin condición de continuidad)
    ingreso_pf_alto: float = 1.6
    ingreso_pf_medio: float = 1.4
    ingreso_pf_bajo: float = 1.0

    # Independiente (ingreso + años de Cámara de Comercio, ambos
    # deben cumplirse para la celda)
    ingreso_i_alto: float = 2.5
    anios_cam_alto: float = 1
    ingreso_i_medio_min: float = 2.0
    anios_cam_medio: float = 2
    ingreso_i_bajo_min: float = 1.6
    anios_cam_bajo: float = 3
    ingreso_i_gris_min: float = 1.4  # exclusivo, > 1.4
    ingreso_i_gris_max: float = 1.6  # exclusivo, < 1.6
    anios_cam_gris: float = 4
    ingreso_i_piso_rechazo: float = 1.4  # <= -> Rechazado

    # --- Política de edad (BRD, confirmada explícita) ---
    edad_minima: int = 18
    edad_maxima: int = 65

    # --- Gastos personales (BRD sección 2.4.4, distinto de la
    # primera versión de este archivo: 40/45/50%, no 35/40/45%) ---
    gastos_personales_pct_alto: float = 40.0   # SMMLV >= 2
    gastos_personales_pct_medio: float = 45.0  # 1.6 <= SMMLV < 2
    gastos_personales_pct_bajo: float = 50.0   # SMMLV < 1.6
    gastos_personales_umbral_alto: float = 2.0
    gastos_personales_umbral_medio: float = 1.6

    # --- Endeudamiento (BRD sección 2.4.8) ---
    endeudamiento_moderado_min_pct: float = 86.0  # rango [86,90] -> Rechazado
    endeudamiento_alto_pct: float = 90.0          # > 90 -> Rechazado

    # --- Capacidad de pago y cupo (BRD sección 2.4.8) ---
    capacidad_pago_pct: float = 70.0  # NO 90% (corregido vs. versión anterior)
    cupo_sugerido_tasa_pct: float = 2.0    # fija, no viene del cliente
    cupo_sugerido_plazo_meses: int = 24    # fijo, no viene del cliente

    # --- Gasto financiero (obligaciones del buró) ---
    tasa_gasto_financiero_pct: float = 2.0
    plazo_rotativo_default_meses: int = 36

    # --- Umbrales de conteo de los filtros duros (BRD tabla 2.4.1) ---
    umbral_mora_30_historica: int = 2   # antes se había asumido 4
    umbral_reestructuraciones: int = 2

    # --- Pendiente (Telcos, sin valor en el BRD) ---
    saldo_mora_be: float | None = None

    def __post_init__(self):
        self._cargar_overrides_de_entorno()

    def _cargar_overrides_de_entorno(self) -> None:
        for f in fields(self):
            crudo = os.getenv(f"{_ENV_PREFIX}{f.name.upper()}")
            if crudo is None:
                continue
            tipo = f.type
            if "float" in str(tipo):
                setattr(self, f.name, float(crudo))
            elif "int" in str(tipo):
                setattr(self, f.name, int(crudo))
