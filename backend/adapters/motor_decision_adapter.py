from sqlalchemy.orm import Session

from backend.services.motor_decision_service import (
    MotorDecisionService,
)
from backend.services.valor_ingreso_service import (
    IngresoPropioService,
)


class MotorDecisionAdapter:
    """
    Adapter del motor de decisión propio de Inversiones Pacíficas.

    Reemplaza el antiguo DatacreditoAdapter: ya no se realizan
    llamadas externas a Preselecta ni a Valor Ingreso de Datacrédito.
    Toda la evaluación de crédito y el cálculo de ingreso se
    resuelven con lógica interna (ver services/motor_decision_service.py
    y services/ingreso_propio_service.py).

    A diferencia del adapter anterior, este NO es un singleton de
    módulo: los servicios necesitan una sesión de base de datos por
    request, así que el adapter se instancia por request en el
    controller (ver controllers/motor_controller.py), inyectando la
    sesión vía Depends(get_db).
    """

    def __init__(self, db: Session) -> None:

        self.motor_decision_service = MotorDecisionService(db)

        self.ingreso_propio_service = IngresoPropioService(db)

    async def evaluar_solicitud(
        self,
        payload: dict,
    ):
        return await self.motor_decision_service.evaluar(
            payload
        )

    async def consultar_ingreso(
        self,
        params: dict,
    ):
        return await self.ingreso_propio_service.consultar(
            params
        )
