"""
Cálculo de capacidad de pago según el BRD original, sección 2.4.8
"Cálculos" (aplican para TODOS los casos, sin importar la decisión
previa de score/ingreso).

Fórmulas confirmadas en el BRD real (distintas en varios puntos de
la primera versión de este archivo, basada en el resumen):

    Gastos personales =
        INGRESO_FINAL * 40%   si INGRESO_FINAL_SMMLV >= 2
        INGRESO_FINAL * 45%   si 1.6 <= INGRESO_FINAL_SMMLV < 2
        INGRESO_FINAL * 50%   si INGRESO_FINAL_SMMLV < 1.6

    Endeudamiento =
        (gasto_rotativo + gasto_no_rotativo + gastos_personales)
        / INGRESO_FINAL * 100
        (nota: el BRD usa solo INGRESO_FINAL en el denominador, NO
        ingreso_final + otros_ingresos)
        -> 86% <= endeudamiento <= 90%: RECHAZADO "Endeudamiento Moderado"
        -> endeudamiento > 90%: RECHAZADO "Endeudamiento Alto"

    Disponible = INGRESO_FINAL - (gasto_rotativo + gasto_no_rotativo
                                   + gastos_personales)
        -> <= 0: RECHAZADO "Sin Disponible"

    Capacidad de pago = Disponible * 70%   (NO 90%)
        -> <= 0: RECHAZADO "Sin Capacidad de Pago"

    Cupo sugerido = valor_presente_anualidad(capacidad_de_pago,
                                              tasa=2%, plazo=24)
        (tasa y plazo FIJOS del BRD, no vienen del cliente)

    Cuota sugerida = cuota_anualidad(cupo_sugerido, tasa_entrada,
                                      plazo_entrada)
        (aquí sí tasa/plazo son "valor de entrada", es decir, los
        que manda el cliente en la solicitud)

El gasto financiero (rotativo y no rotativo) sigue dependiendo de
obligaciones del buró que hoy no están mapeadas en db_models/ (ver
nota en la clase ObligacionBuro más abajo) — eso no cambió.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.repositories.solicitud_repository import (
    SolicitudRepository,
)
from backend.services.finanzas import (
    cuota_a_valor_mensual,
    cuota_anualidad,
    valor_presente_anualidad,
)
from backend.services.motor_exceptions import ReglaNoDefinidaError
from backend.services.motor_parametros import MotorParametros
from backend.utils.loggers import get_logger


logger = get_logger("motor_decision.capacidad_pago")


@dataclass
class ObligacionBuro:
    """
    Una obligación financiera vigente reportada en el buró. No hay
    tabla en el esquema que la respalde todavía — se recibe como
    parámetro (ver nota de arquitectura en el módulo).
    """
    es_rotativa: bool  # tarjeta de crédito / cartera rotativa (carteras 2 y 3)
    cuota_reportada: float | None
    periodicidad: str | None
    cupo_o_saldo: float | None = None
    fecha_apertura_dias: int | None = None


@dataclass
class ResultadoCapacidadPago:
    gastos_personales: float
    gasto_financiero_no_rotativo: float
    gasto_financiero_rotativo: float
    endeudamiento_pct: float
    disponible: float
    capacidad_de_pago: float
    cupo_sugerido: float | None
    rechazado: bool
    causal_codigo: str | None
    causal_descripcion: str | None


def calcular_gastos_personales(
    ingreso_final: float,
    ingreso_final_smmlv: float,
    params: MotorParametros,
) -> float:
    if ingreso_final_smmlv >= params.gastos_personales_umbral_alto:
        return ingreso_final * (params.gastos_personales_pct_alto / 100)
    if ingreso_final_smmlv >= params.gastos_personales_umbral_medio:
        return ingreso_final * (params.gastos_personales_pct_medio / 100)
    return ingreso_final * (params.gastos_personales_pct_bajo / 100)


def calcular_gasto_no_rotativo(
    obligaciones: list[ObligacionBuro],
    params: MotorParametros,
) -> float:
    total = 0.0
    for obligacion in obligaciones:
        if obligacion.es_rotativa:
            continue
        if obligacion.cuota_reportada:
            total += cuota_a_valor_mensual(
                obligacion.cuota_reportada,
                obligacion.periodicidad or "mensual",
            )
            continue
        if obligacion.cupo_o_saldo and obligacion.fecha_apertura_dias:
            plazo_meses = max(1, round(obligacion.fecha_apertura_dias / 30))
            total += cuota_anualidad(
                obligacion.cupo_o_saldo,
                params.tasa_gasto_financiero_pct,
                plazo_meses,
            )
    return total


def calcular_gasto_rotativo(
    obligaciones: list[ObligacionBuro],
    params: MotorParametros,
) -> float:
    total = 0.0
    for obligacion in obligaciones:
        if not obligacion.es_rotativa:
            continue
        if obligacion.cuota_reportada:
            total += obligacion.cuota_reportada
            continue
        if obligacion.cupo_o_saldo:
            total += cuota_anualidad(
                obligacion.cupo_o_saldo,
                params.tasa_gasto_financiero_pct,
                params.plazo_rotativo_default_meses,
            )
    return total


def calcular_capacidad_pago(
    ingreso_final: float,
    ingreso_final_smmlv: float,
    gasto_financiero_no_rotativo: float,
    gasto_financiero_rotativo: float,
    params: MotorParametros,
) -> ResultadoCapacidadPago:

    gastos_personales = calcular_gastos_personales(
        ingreso_final, ingreso_final_smmlv, params
    )
    gasto_financiero_total = (
        gasto_financiero_rotativo + gasto_financiero_no_rotativo
    )

    endeudamiento_pct = (
        (gasto_financiero_total + gastos_personales) / ingreso_final * 100
        if ingreso_final > 0
        else 100.0
    )

    if endeudamiento_pct > params.endeudamiento_alto_pct:
        return ResultadoCapacidadPago(
            gastos_personales, gasto_financiero_no_rotativo,
            gasto_financiero_rotativo, endeudamiento_pct,
            disponible=0, capacidad_de_pago=0, cupo_sugerido=None,
            rechazado=True,
            causal_codigo="ENDEUDAMIENTO_ALTO",
            causal_descripcion="Endeudamiento Alto",
        )
    if endeudamiento_pct >= params.endeudamiento_moderado_min_pct:
        return ResultadoCapacidadPago(
            gastos_personales, gasto_financiero_no_rotativo,
            gasto_financiero_rotativo, endeudamiento_pct,
            disponible=0, capacidad_de_pago=0, cupo_sugerido=None,
            rechazado=True,
            causal_codigo="ENDEUDAMIENTO_MODERADO",
            causal_descripcion="Endeudamiento Moderado",
        )

    disponible = ingreso_final - (gasto_financiero_total + gastos_personales)

    if disponible <= 0:
        return ResultadoCapacidadPago(
            gastos_personales, gasto_financiero_no_rotativo,
            gasto_financiero_rotativo, endeudamiento_pct,
            disponible=disponible, capacidad_de_pago=0, cupo_sugerido=None,
            rechazado=True,
            causal_codigo="SIN_DISPONIBLE",
            causal_descripcion="Sin Disponible",
        )

    capacidad_de_pago = disponible * (params.capacidad_pago_pct / 100)

    if capacidad_de_pago <= 0:
        return ResultadoCapacidadPago(
            gastos_personales, gasto_financiero_no_rotativo,
            gasto_financiero_rotativo, endeudamiento_pct,
            disponible=disponible, capacidad_de_pago=capacidad_de_pago,
            cupo_sugerido=None, rechazado=True,
            causal_codigo="SIN_CAPACIDAD_PAGO",
            causal_descripcion="Sin Capacidad de Pago",
        )

    cupo_sugerido = valor_presente_anualidad(
        capacidad_de_pago,
        params.cupo_sugerido_tasa_pct,
        params.cupo_sugerido_plazo_meses,
    )

    return ResultadoCapacidadPago(
        gastos_personales, gasto_financiero_no_rotativo,
        gasto_financiero_rotativo, endeudamiento_pct,
        disponible=disponible, capacidad_de_pago=capacidad_de_pago,
        cupo_sugerido=cupo_sugerido, rechazado=False,
        causal_codigo=None, causal_descripcion=None,
    )


def calcular_cuota_sugerida(
    cupo_sugerido: float,
    tasa_pct: float,
    plazo_meses: int,
) -> float:
    """
    A diferencia del cupo sugerido (tasa/plazo fijos del BRD), la
    cuota sugerida SÍ usa la tasa y el plazo que manda el cliente en
    la solicitud ("Valor de entrada", según el BRD).
    """
    return cuota_anualidad(cupo_sugerido, tasa_pct, plazo_meses)


def validar_capacidad_para_moto(
    cuota_moto: float,
    cuota_sugerida: float,
) -> tuple[bool, str | None, str | None]:
    if cuota_moto > cuota_sugerida:
        return False, "SIN_CAPACIDAD_MOTO", "Sin Capacidad para moto Solicitada"
    return True, None, None


class CapacidadPagoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.solicitud_repo = SolicitudRepository(db)

    async def calcular(
        self,
        id_solicitud: uuid.UUID,
        ingreso_final: float,
        salario_minimo: float,
        gasto_financiero_no_rotativo: float,
        gasto_financiero_rotativo: float,
        params: MotorParametros,
    ) -> ResultadoCapacidadPago:

        solicitud = self.solicitud_repo.obtener_con_datos_para_evaluar(
            id_solicitud
        )
        if solicitud is None:
            raise ValueError(f"No existe la solicitud {id_solicitud}")
        if salario_minimo <= 0:
            raise ReglaNoDefinidaError(
                "salario_minimo debe ser mayor que cero."
            )

        ingreso_final_smmlv = ingreso_final / salario_minimo

        return calcular_capacidad_pago(
            ingreso_final=ingreso_final,
            ingreso_final_smmlv=ingreso_final_smmlv,
            gasto_financiero_no_rotativo=gasto_financiero_no_rotativo,
            gasto_financiero_rotativo=gasto_financiero_rotativo,
            params=params,
        )
