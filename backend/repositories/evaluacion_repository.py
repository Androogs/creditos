import uuid

from sqlalchemy.orm import Session

from backend.db_models.models import (
    CriterioEvaluacion,
    EvaluacionCredito,
    EvaluacionDetalle,
)


class EvaluacionRepository:
    """
    Escritura de evaluacion_credito y evaluacion_detalle.

    No hace falta desmarcar manualmente versiones anteriores como
    'vigente = false': eso ya lo hace el trigger
    trg_evaluacion_vigente (desmarcar_versiones_previas()) definido
    en schema.sql en cuanto se inserta una nueva fila vigente.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_criterios(self) -> list[CriterioEvaluacion]:
        return self.db.query(CriterioEvaluacion).all()

    def crear_evaluacion(
        self,
        id_solicitud: uuid.UUID,
        score: float | None,
        detalles: list[dict],
        **campos_evaluacion,
    ) -> EvaluacionCredito:
        """
        detalles: lista de dicts con las llaves
        {id_criterio, resultado, puntaje, causal}, uno por cada
        criterio evaluado.
        """

        ultima_version = (
            self.db.query(EvaluacionCredito)
            .filter(EvaluacionCredito.id_solicitud == id_solicitud)
            .order_by(EvaluacionCredito.version.desc())
            .first()
        )
        nueva_version = (
            ultima_version.version + 1 if ultima_version else 1
        )

        evaluacion = EvaluacionCredito(
            id_solicitud=id_solicitud,
            version=nueva_version,
            vigente=True,
            score=score,
            **campos_evaluacion,
        )
        self.db.add(evaluacion)
        self.db.flush()  # necesitamos evaluacion.id_evaluacion

        for detalle in detalles:
            self.db.add(
                EvaluacionDetalle(
                    id_evaluacion=evaluacion.id_evaluacion,
                    id_criterio=detalle["id_criterio"],
                    resultado=detalle["resultado"],
                    puntaje=detalle.get("puntaje"),
                    causal=detalle.get("causal"),
                )
            )

        self.db.flush()
        return evaluacion
