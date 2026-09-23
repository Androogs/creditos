from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.adapters.motor_decision_adapter import (
    MotorDecisionAdapter,
)
from backend.database.session import get_db
from backend.models.motor_models import (
    EvaluarSolicitudRequest,
    IngresoPropioRequest,
)


router = APIRouter(
    prefix="/motor",
    tags=["Motor de decisión"],
)


@router.post("/evaluar")
async def evaluar_solicitud(
    request: EvaluarSolicitudRequest,
    db: Session = Depends(get_db),
):
    """
    Reemplaza el antiguo POST /datacredito/preselecta/decision.
    Corre el motor de decisión propio sobre los datos de la solicitud.
    """
    payload = request.model_dump(exclude_none=True)
    adapter = MotorDecisionAdapter(db)

    resultado = await adapter.evaluar_solicitud(payload)
    db.commit()
    return resultado


@router.post("/ingreso")
async def consultar_ingreso(
    request: IngresoPropioRequest,
    db: Session = Depends(get_db),
):
    """
    Reemplaza el antiguo POST /datacredito/valor-ingreso.
    Calcula el ingreso propio del cliente a partir de cotizante /
    cotizante_ingreso_mensual, sin depender de Datacrédito.
    """
    params = request.model_dump()
    adapter = MotorDecisionAdapter(db)

    return await adapter.consultar_ingreso(params)
