import uuid

from sqlalchemy.orm import Session

from backend.db_models.models import CapacidadPago
from backend.repositories.solicitud_repository import (
    SolicitudRepository,
)
from backend.services.motor_exceptions import ReglaNoDefinidaError
from backend.utils.loggers import get_logger


logger = get_logger("motor_decision.capacidad_pago")


class CapacidadPagoService:
    """
    Cálculo de capacidad de pago. Llena la tabla capacidad_pago
    (salario_minimo, ingreso_final, gastos_personales, disponible_1,
    capacidad_pago_2, cupo_calculado, cupo_aprobado), que hoy existe
    en el esquema pero sin ninguna fórmula implementada en código.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.solicitud_repo = SolicitudRepository(db)

    async def calcular(
        self,
        id_solicitud: uuid.UUID,
        ingreso_final: float,
        salario_minimo: float,
    ) -> CapacidadPago:

        solicitud = self.solicitud_repo.obtener_con_datos_para_evaluar(
            id_solicitud
        )
        if solicitud is None:
            raise ValueError(f"No existe la solicitud {id_solicitud}")

        # TODO: definir con los manuales del motor propio:
        #   - fórmula de gastos_personales (¿tabla fija por SMLMV +
        #     personas a cargo? ¿porcentaje del ingreso?)
        #   - fórmula de disponible_1 (típicamente
        #     ingreso_final - gastos_personales, a confirmar)
        #   - fórmula de capacidad_pago_2 (¿aplica algún
        #     porcentaje máximo de compromiso, ej. 30-40% del
        #     disponible?)
        #   - tasa_cupo / plazo_cupo (parámetros del producto o
        #     de la política de riesgo)
        #   - cupo_calculado a partir de tasa_cupo/plazo_cupo y
        #     capacidad_pago_2 (fórmula de anualidad estándar,
        #     pero el porcentaje de la cuota máxima permitida sobre
        #     el disponible es una decisión de negocio pendiente)
        raise ReglaNoDefinidaError(
            "No hay fórmula de capacidad de pago definida todavía."
        )
