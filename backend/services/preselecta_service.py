import os

import httpx

from backend.services.datacredito_auth import (
    DatacreditoAuthService,
)
from backend.utils.loggers import get_logger
from backend.utils.tls import load_certificates


logger = get_logger("datacredito.preselecta")


class PreselectaService:

    def __init__(self) -> None:

        self.auth = DatacreditoAuthService(
            "preselecta"
        )

        self.url = os.getenv(
            "DATACREDITO_PRESELECTA_SERVICE_URL"
        )

    async def decision(self, payload: dict):

        if not self.url:
            raise RuntimeError(
                "Falta la variable "
                "DATACREDITO_PRESELECTA_SERVICE_URL"
            )

        token = await self.auth.get_access_token()

        headers = {
            "access_token": token,
            "client_id": os.getenv(
                "DATACREDITO_PRESELECTA_CLIENT_ID"
            ),
            "client_secret": os.getenv(
                "DATACREDITO_PRESELECTA_CLIENT_SECRET"
            ),
            "Content-Type": "application/json",
            "Accept": "application/json",
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

                response = await client.post(
                    self.url,
                    json=payload,
                    headers=headers,
                )

            if response.status_code in (401, 403):

                logger.warning(
                    "Token de Preselecta rechazado. "
                    "Renovando token."
                )

                self.auth.clear_token()

                token = await self.auth.get_access_token()

                headers["access_token"] = token

                async with httpx.AsyncClient(
                    verify=verify,
                    timeout=timeout,
                ) as client:

                    response = await client.post(
                        self.url,
                        json=payload,
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
                "Error consultando Preselecta: %s",
                error,
            )

            raise RuntimeError(
                "Error consumiendo servicio Preselecta"
            ) from error