import base64
import os
import time

import httpx

from backend.utils.loggers import get_logger
from backend.utils.tls import load_certificates


logger = get_logger("datacredito.auth")


class DatacreditoAuthService:

    def __init__(self, environment: str) -> None:

        if environment not in ("preselecta", "income"):
            raise ValueError(
                f"Ambiente Datacrédito no soportado: {environment}"
            )

        self.environment = environment

        if environment == "preselecta":

            self.token_url = os.getenv(
                "DATACREDITO_PRESELECTA_TOKEN_URL"
            )

            self.client_id = os.getenv(
                "DATACREDITO_PRESELECTA_CLIENT_ID"
            )

            self.client_secret = os.getenv(
                "DATACREDITO_PRESELECTA_CLIENT_SECRET"
            )

            self.username = os.getenv(
                "DATACREDITO_PRESELECTA_USERNAME"
            )

            self.password = os.getenv(
                "DATACREDITO_PRESELECTA_PASSWORD"
            )

            self.scope = os.getenv(
                "DATACREDITO_PRESELECTA_SCOPE",
                "expco_preselecta",
            )

        else:

            self.token_url = os.getenv(
                "DATACREDITO_INCOME_TOKEN_URL"
            )

            self.client_id = os.getenv(
                "DATACREDITO_INCOME_CLIENT_ID"
            )

            self.client_secret = os.getenv(
                "DATACREDITO_INCOME_CLIENT_SECRET"
            )

            self.username = os.getenv(
                "DATACREDITO_INCOME_USERNAME"
            )

            self.password = os.getenv(
                "DATACREDITO_INCOME_PASSWORD"
            )

            self.scope = os.getenv(
                "DATACREDITO_INCOME_SCOPE",
                "expco_incomes",
            )

        self.access_token: str | None = None
        self.expires_at: float = 0

    async def get_access_token(self) -> str:

        if (
            self.access_token
            and time.time() < self.expires_at
        ):
            return self.access_token

        return await self._request_token()

    async def _request_token(self) -> str:

        required_values = {
            "token_url": self.token_url,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }

        missing_values = [
            name
            for name, value in required_values.items()
            if not value
        ]

        if missing_values:
            raise RuntimeError(
                "Faltan variables de configuración de "
                f"Datacrédito para {self.environment}: "
                + ", ".join(missing_values)
            )

        credentials = (
            f"{self.client_id}:{self.client_secret}"
        )

        encoded_credentials = base64.b64encode(
            credentials.encode()
        ).decode()

        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "scope": self.scope,
        }

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
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

            logger.info(
                "Solicitando access_token para %s",
                self.environment,
            )

            async with httpx.AsyncClient(
                verify=verify,
                timeout=timeout,
            ) as client:

                response = await client.post(
                    self.token_url,
                    data=data,
                    headers=headers,
                )

            response.raise_for_status()

            result = response.json()

            token = result.get("access_token")

            if not token:
                raise RuntimeError(
                    "Datacrédito no retornó access_token"
                )

            expires_in = int(
                result.get(
                    "expires_in",
                    3600,
                )
            )

            self.access_token = token

            self.expires_at = (
                time.time()
                + max(
                    0,
                    expires_in - 60,
                )
            )

            logger.info(
                "Access token obtenido correctamente"
            )

            return token

        except httpx.HTTPError as error:

            logger.error(
                "Error de autenticación Datacrédito: %s",
                error,
            )

            raise RuntimeError(
                "No fue posible autenticar "
                "contra Datacrédito"
            ) from error

    def clear_token(self) -> None:

        self.access_token = None
        self.expires_at = 0