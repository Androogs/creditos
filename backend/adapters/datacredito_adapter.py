from backend.services.preselecta_service import (
    PreselectaService,
)
from backend.services.valor_ingreso_service import (
    ValorIngresoService,
)


class DatacreditoAdapter:

    def __init__(self) -> None:

        self.preselecta_service = PreselectaService()

        self.valor_ingreso_service = (
            ValorIngresoService()
        )

    async def consultar_preselecta(
        self,
        payload: dict,
    ):
        return await self.preselecta_service.decision(
            payload
        )

    async def consultar_valor_ingreso(
        self,
        params: dict,
    ):
        return await self.valor_ingreso_service.consultar(
            params
        )


datacredito_adapter = DatacreditoAdapter()