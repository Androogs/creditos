import uuid
from statistics import mean, median

from sqlalchemy.orm import Session

from backend.repositories.solicitud_repository import (
    SolicitudRepository,
)
from backend.utils.loggers import get_logger


logger = get_logger("motor_decision.ingreso_propio")


class IngresoPropioService:
    """
    Cálculo de ingreso propio del cliente. Reemplaza la llamada a
    ValorIngresoService.consultar() (Datacrédito).

    Se apoya en cotizante / cotizante_ingreso_mensual, ya cargados
    en la solicitud, para calcular promedio/mediana de ingresos.

    El cálculo del promedio simple y la mediana SÍ se implementan
    aquí porque son operaciones estadísticas estándar, no reglas de
    negocio propietarias. Lo que queda pendiente (ver TODO abajo) es
    la política de negocio sobre qué métrica usar como
    'ingreso_final' y cómo tratar independientes vs. empleados.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.solicitud_repo = SolicitudRepository(db)

    async def consultar(self, params: dict) -> dict:

        id_solicitud = uuid.UUID(str(params["id_solicitud"]))
        meses_a_promediar = int(params.get("meses_a_promediar", 3))

        logger.info(
            "Consulta de ingreso propio solicitada",
            extra={"id_solicitud": str(id_solicitud)},
        )

        solicitud = self.solicitud_repo.obtener_con_datos_para_evaluar(
            id_solicitud
        )
        if solicitud is None:
            raise ValueError(
                f"No existe la solicitud {id_solicitud}"
            )

        resultados_por_cotizante = []
        for cotizante in solicitud.cotizantes:
            ingresos_recientes = sorted(
                cotizante.ingresos_mensuales,
                key=lambda i: i.periodo,
                reverse=True,
            )[:meses_a_promediar]

            valores = [float(i.ingreso) for i in ingresos_recientes]

            if not valores:
                continue

            resultados_por_cotizante.append(
                {
                    "razon_social_aportante": cotizante.razon_social_aportante,
                    "promedio": mean(valores),
                    "mediana": median(valores),
                    "meses_considerados": len(valores),
                }
            )

        # TODO: definir con los manuales del motor propio cuál es
        # la política de negocio para consolidar 'ingreso_final'
        # cuando hay varios cotizantes (¿se suman?, ¿se pondera por
        # antigüedad?, ¿se descarta el de menor continuidad?) y cómo
        # se trata el caso de independientes sin cotizante formal
        # (datos_laborales.ingreso_mensual como fuente alterna).
        #
        # Por ahora se devuelve el detalle por cotizante sin
        # consolidar, para que el consumidor de la API decida hasta
        # que la regla esté definida.

        return {
            "id_solicitud": str(id_solicitud),
            "por_cotizante": resultados_por_cotizante,
            "ingreso_final": None,
        }
