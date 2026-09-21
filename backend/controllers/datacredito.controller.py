from fastapi import APIRouter

from backend.adapters.datacredito_adapter import (
    datacredito_adapter
)

from backend.models.datacredito_models import (
    PreselectaRequest,
    ValorIngresoRequest
)


router = APIRouter(
    prefix="/datacredito",
    tags=["Datacrédito"]
)


@router.post(
    "/preselecta/decision"
)
async def consultar_preselecta(
    request: PreselectaRequest
):

    payload = request.model_dump(
        exclude_none=True
    )

    return await (
        datacredito_adapter
        .consultar_preselecta(
            payload
        )
    )


@router.post(
    "/valor-ingreso"
)
async def consultar_valor_ingreso(
    request: ValorIngresoRequest
):

    params = request.model_dump()

    return await (
        datacredito_adapter
        .consultar_valor_ingreso(
            params
        )
    )