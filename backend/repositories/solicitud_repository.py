import uuid

from sqlalchemy.orm import Session, joinedload

from backend.db_models.models import SolicitudCredito


class SolicitudRepository:
    """
    Lectura/escritura de solicitud_credito y sus relaciones directas.
    Centraliza los joins que el motor de decisión necesita para no
    repetir queries dispersas en los services.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener_con_datos_para_evaluar(
        self,
        id_solicitud: uuid.UUID,
    ) -> SolicitudCredito | None:
        return (
            self.db.query(SolicitudCredito)
            .options(
                joinedload(SolicitudCredito.cliente),
                joinedload(SolicitudCredito.datos_laborales),
                joinedload(SolicitudCredito.contacto_vivienda),
                joinedload(SolicitudCredito.cotizantes),
            )
            .filter(SolicitudCredito.id_solicitud == id_solicitud)
            .one_or_none()
        )

    def actualizar_decision(
        self,
        id_solicitud: uuid.UUID,
        decision: str,
        descripcion_estado: str | None = None,
    ) -> None:
        solicitud = (
            self.db.query(SolicitudCredito)
            .filter(SolicitudCredito.id_solicitud == id_solicitud)
            .one()
        )
        solicitud.decision = decision
        if descripcion_estado is not None:
            solicitud.descripcion_estado = descripcion_estado
        self.db.flush()
