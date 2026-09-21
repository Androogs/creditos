import os

import httpx

from backend.services.datacredito_auth import (
    DatacreditoAuthService,
)
from backend.utils.loggers import get_logger
from backend.utils.tls import load_certificates


logger = get_logger("datacredito.income")


class ValorIngresoService:

    def __init__(self) -> None:

        self.auth = DatacreditoAuthService(
            "income"
        )

        self.url = os.getenv(
            "DATACREDITO_INCOME_SERVICE_URL"
        )

    async def consultar(self, params: dict):

        if not self.url:
            raise RuntimeError(
                "Falta la variable "
                "DATACREDITO_INCOME_SERVICE_URL"
            )

        token = await self.auth.get_access_token()

        headers = {
            "access_token": token,
            "client_id": os.getenv(
                "DATACREDITO_INCOME_CLIENT_ID"
            ),
            "client_secret": os.getenv(
                "DATACREDITO_INCOME_CLIENT_SECRET"
            ),
            "Accept": "application/json",
            "Accept-Encoding": "gzip,deflate",
        }

        verify = load_certificates()

        timeout = (
            float(
                os.getenv(
                    "DATACREDITO_TIMEOUT",
                    "30000",
                )
            )
            / 1000
        )

        try:

            async with httpx.AsyncClient(
                verify=verify,
                timeout=timeout,
            ) as client:

                response = await client.get(
                    self.url,
                    params=params,
                    headers=headers,
                )

            if response.status_code in (401, 403):

                logger.warning(
                    "Token de Valor Ingreso rechazado. "
                    "Renovando token."
                )

                self.auth.clear_token()

                token = await self.auth.get_access_token()

                headers["access_token"] = token

                async with httpx.AsyncClient(
                    verify=verify,
                    timeout=timeout,
                ) as client:

                    response = await client.get(
                        self.url,
                        params=params,
                        headers=headers,
                    )

            response.raise_for_status()

            return {
                "success": True,
                "status": response.status_code,
                "data": response.json(),
            }

        except httpx.HTTPError as error:

            logger.error(
                "Error consultando Valor Ingreso: %s",
                error,
            )

            raise RuntimeError(
                "Error consumiendo servicio "
                "Valor Ingreso"
            ) from error