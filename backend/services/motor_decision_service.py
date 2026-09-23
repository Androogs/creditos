import uuid

from sqlalchemy.orm import Session

from backend.db_models.models import SolicitudCredito
from backend.repositories.evaluacion_repository import (
    EvaluacionRepository,
)
from backend.repositories.solicitud_repository import (
    SolicitudRepository,
)
from backend.services.motor_exceptions import ReglaNoDefinidaError
from backend.utils.loggers import get_logger


logger = get_logger("motor_decision.propio")


class MotorDecisionService:
    """
    Motor de decisión propio de Inversiones Pacíficas.

    Reemplaza la llamada a PreselectaService.decision(). El flujo
    general (pasos 1-4) ya está implementado sobre las tablas reales
    del esquema; lo que falta en cada paso es la fórmula de negocio
    (marcada con ReglaNoDefinidaError), pendiente de los manuales
    del motor propio.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.solicitud_repo = SolicitudRepository(db)
        self.evaluacion_repo = EvaluacionRepository(db)

    async def evaluar(self, payload: dict) -> dict:

        id_solicitud = uuid.UUID(str(payload["id_solicitud"]))

        logger.info(
            "Evaluación motor propio solicitada",
            extra={"id_solicitud": str(id_solicitud)},
        )

        # Paso 1: cargar la solicitud con todo lo necesario para
        # evaluar (cliente, datos laborales, vivienda, cotizantes).
        solicitud = self.solicitud_repo.obtener_con_datos_para_evaluar(
            id_solicitud
        )
        if solicitud is None:
            raise ValueError(
                f"No existe la solicitud {id_solicitud}"
            )

        # Paso 2: evaluar cada criterio de criterio_evaluacion.
        criterios = self.evaluacion_repo.obtener_criterios()
        detalles = []
        for criterio in criterios:
            resultado, puntaje, causal = self._evaluar_criterio(
                criterio.codigo, solicitud
            )
            detalles.append(
                {
                    "id_criterio": criterio.id_criterio,
                    "resultado": resultado,
                    "puntaje": puntaje,
                    "causal": causal,
                }
            )

        # Paso 3: calcular score agregado.
        score = self._calcular_score(detalles)

        # Paso 4: registrar la evaluación (versionada, escribe
        # evaluacion_credito + evaluacion_detalle).
        evaluacion = self.evaluacion_repo.crear_evaluacion(
            id_solicitud=id_solicitud,
            score=score,
            detalles=detalles,
        )

        # Paso 5: decidir aprobado / rechazado / perfil_gris.
        decision = self._decidir(score, detalles)

        self.solicitud_repo.actualizar_decision(
            id_solicitud=id_solicitud,
            decision=decision,
        )

        return {
            "id_solicitud": str(id_solicitud),
            "id_evaluacion": evaluacion.id_evaluacion,
            "version": evaluacion.version,
            "score": score,
            "decision": decision,
            "detalles": detalles,
        }

    def _evaluar_criterio(
        self,
        codigo: str,
        solicitud: SolicitudCredito,
    ) -> tuple[bool, float | None, str | None]:
        """
        Evalúa un criterio individual contra los datos de la
        solicitud. Devuelve (resultado, puntaje, causal).

        TODO: implementar la regla real de cada codigo de
        criterio_evaluacion una vez definidas en los manuales del
        motor propio. Ejemplo de cómo debería verse cuando esté
        definida la regla de edad:

            if codigo == "EDAD_POLITICA":
                edad = _calcular_edad(solicitud.cliente.fecha_nacimiento)
                cumple = 18 <= edad <= 65
                causal = None if cumple else "Edad fuera de rango"
                return cumple, None, causal

        Por ahora, cualquier criterio sin regla implementada
        interrumpe la evaluación con un 501 explícito en vez de
        devolver un resultado inventado.
        """
        raise ReglaNoDefinidaError(
            f"No hay regla de negocio definida todavía para el "
            f"criterio '{codigo}'. Pendiente de los manuales del "
            f"motor propio."
        )

    def _calcular_score(self, detalles: list[dict]) -> float | None:
        """
        TODO: definir la fórmula de agregación de score (suma
        ponderada, promedio, modelo estadístico, etc.) según los
        manuales del motor propio. Los puntajes individuales ya
        están disponibles en detalles[i]['puntaje'].
        """
        raise ReglaNoDefinidaError(
            "No hay fórmula de agregación de score definida todavía."
        )

    def _decidir(
        self,
        score: float | None,
        detalles: list[dict],
    ) -> str:
        """
        TODO: definir los puntos de corte que determinan
        'aprobado' / 'rechazado' / 'perfil_gris' según el score y
        las causales duras (por ejemplo, un solo criterio 'buro'
        incumplido podría rechazar automáticamente sin importar el
        score, dependiendo de la política que definan los manuales).
        """
        raise ReglaNoDefinidaError(
            "No hay puntos de corte de decisión definidos todavía."
        )
