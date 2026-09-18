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
