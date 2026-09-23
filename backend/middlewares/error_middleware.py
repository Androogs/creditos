from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.services.motor_exceptions import (
    ReglaNoDefinidaError,
)


def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(ReglaNoDefinidaError)
    async def handle_regla_no_definida(
        _request: Request,
        exception: ReglaNoDefinidaError,
    ) -> JSONResponse:
        # 501: la ruta existe y el contrato es válido, pero la
        # lógica de negocio (fórmula/regla) todavía no está
        # implementada porque depende de los manuales pendientes.
        return JSONResponse(
            status_code=501,
            content={"detail": str(exception)},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        _request: Request,
        _exception: Exception,
    ) -> JSONResponse:

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error"
            },
        )
