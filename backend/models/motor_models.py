from uuid import UUID

from pydantic import BaseModel


class EvaluarSolicitudRequest(BaseModel):
    """
    Entrada para /motor/evaluar.

    El motor propio opera sobre una solicitud ya existente en
    solicitud_credito (con sus datos_laborales, cotizante y
    solicitud_contacto_vivienda ya cargados), por eso el payload de
    entrada es mínimo: solo referencia a la solicitud.

    TODO: ampliar si los manuales de reglas definen parámetros
    adicionales que deban enviarse en el momento de evaluar
    (por ejemplo, forzar una versión específica de reglas o un
    modo de simulación).
    """

    id_solicitud: UUID


class IngresoPropioRequest(BaseModel):
    """
    Entrada para /motor/ingreso.

    Reemplaza a ValorIngresoRequest (Datacrédito). El cálculo se
    hace sobre cotizante / cotizante_ingreso_mensual ya almacenados
    para la solicitud.

    TODO: confirmar con los manuales si se requiere parametrizar el
    número de meses a promediar o el tratamiento de independientes
    vs. empleados.
    """

    id_solicitud: UUID
    meses_a_promediar: int = 3
