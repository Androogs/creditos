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
from typing import Any


class DatacreditoAdapter:
	async def consultar_preselecta(
		self,
		payload: dict[str, Any]
	) -> dict[str, Any]:
		raise NotImplementedError(
			"La integración Python de Preselecta aún no está configurada"
		)

	async def consultar_valor_ingreso(
		self,
		params: dict[str, Any]
	) -> dict[str, Any]:
		raise NotImplementedError(
			"La integración Python de Valor Ingreso aún no está configurada"
		)


datacredito_adapter = DatacreditoAdapter()
