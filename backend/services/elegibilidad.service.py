import uuid
from typing import Any

from sqlalchemy.orm import Session

from backend.db_models.models import (
    AliadoProducto,
    OfertaCredito,
)
from backend.utils.loggers import get_logger


logger = get_logger("motor_decision.elegibilidad")


_OPERADORES = {
    ">=": lambda valor, esperado: valor is not None and valor >= esperado,
    "<=": lambda valor, esperado: valor is not None and valor <= esperado,
    "=": lambda valor, esperado: valor == esperado,
    "!=": lambda valor, esperado: valor != esperado,
    "IN": lambda valor, esperado: valor in esperado,
    "NOT IN": lambda valor, esperado: valor not in esperado,
}


class EligibilidadService:
    """
    Motor de reglas de elegibilidad por producto de aliado.

    A diferencia del motor de decisión (score/capacidad de pago),
    aquí la mecánica SÍ se puede implementar de forma genérica: cada
    fila de aliado_regla_elegibilidad ya trae {campo, operador,
    valor_json}, y los operadores soportados están fijados por el
    CHECK de schema.sql (>=, <=, =, !=, IN, NOT IN).

    Lo que queda pendiente (ver TODO en _obtener_valor_campo) es el
    diccionario de qué 'campo' de negocio corresponde a qué dato
    real de la solicitud/evaluación — eso depende de cómo se
    nombren los campos en los manuales del motor propio.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    async def evaluar_producto(
        self,
        id_solicitud: uuid.UUID,
        producto: AliadoProducto,
        datos_solicitud: dict[str, Any],
    ) -> OfertaCredito:
        """
        datos_solicitud: diccionario ya resuelto con los valores de
        la solicitud/evaluación/capacidad de pago que las reglas
        pueden necesitar, ej.:
            {"score": 720, "ingreso_final": 2500000, "edad": 34}
        """

        motivos_no_elegible = []

        for regla in producto.reglas:
            valor_actual = self._obtener_valor_campo(
                regla.campo, datos_solicitud
            )
            operador_fn = _OPERADORES.get(regla.operador)

            if operador_fn is None:
                raise ValueError(
                    f"Operador no soportado: {regla.operador}"
                )

            cumple = operador_fn(valor_actual, regla.valor_json)

            if not cumple:
                motivos_no_elegible.append(
                    f"{regla.campo} {regla.operador} "
                    f"{regla.valor_json} (valor actual: {valor_actual})"
                )

        elegible = not motivos_no_elegible

        return OfertaCredito(
            id_solicitud=id_solicitud,
            id_aliado_producto=producto.id_aliado_producto,
            elegible=elegible,
            motivo_no_elegible=(
                "; ".join(motivos_no_elegible)
                if motivos_no_elegible
                else None
            ),
        )

    def _obtener_valor_campo(
        self,
        campo: str,
        datos_solicitud: dict[str, Any],
    ) -> Any:
        # TODO: confirmar con los manuales el catálogo completo de
        # nombres de 'campo' válidos en aliado_regla_elegibilidad.
        # Hoy se toma directamente del diccionario ya resuelto que
        # le pasa el llamador (motor_decision_service tras evaluar),
        # sin validar contra una lista cerrada de campos permitidos.
        if campo not in datos_solicitud:
            logger.warning(
                "Campo de regla de elegibilidad no encontrado "
                "en los datos de la solicitud: %s",
                campo,
            )
        return datos_solicitud.get(campo)
