from sqlalchemy.orm import Session

from backend.services.motor_decision_service import MotorDecisionService
from backend.services.valor_ingreso_service import IngresoPropioService


class MotorDecisionAdapter:
    def __init__(self, db: Session) -> None:
        self.motor_decision_service = MotorDecisionService(db)
        self.ingreso_propio_service = IngresoPropioService(db)

    async def evaluar_solicitud(
        self,
        payload: dict,
    ):
        return await self.motor_decision_service.evaluar(payload)

    async def consultar_ingreso(
        self,
        params: dict,
    ):
        return await self.ingreso_propio_service.consultar(params)