import uuid

from sqlalchemy.orm import Session, joinedload

from backend.db_models.models import (
    Cliente,
    DatosLaborales,
    OfertaCredito,
    SolicitudContactoVivienda,
    SolicitudCredito,
)


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

    def obtener_o_crear_cliente(
        self,
        num_cedula: str,
        datos_cliente: dict,
    ) -> Cliente:
        """
        Busca por num_cedula (único en el esquema); si no existe,
        crea el cliente. No actualiza datos de un cliente existente
        aquí a propósito: eso debería ser una operación explícita
        de "actualizar cliente", no un side-effect de crear una
        solicitud nueva.
        """
        cliente = (
            self.db.query(Cliente)
            .filter(Cliente.num_cedula == num_cedula)
            .one_or_none()
        )
        if cliente is not None:
            return cliente

        cliente = Cliente(num_cedula=num_cedula, **datos_cliente)
        self.db.add(cliente)
        self.db.flush()  # necesitamos cliente.id_cliente
        return cliente

    def crear_solicitud(
        self,
        id_cliente: int,
        moneda: str,
        datos_laborales: dict,
        contacto_vivienda: dict,
    ) -> SolicitudCredito:
        solicitud = SolicitudCredito(
            id_cliente=id_cliente,
            moneda=moneda,
        )
        self.db.add(solicitud)
        self.db.flush()  # necesitamos id_solicitud (gen_random_uuid)

        self.db.add(
            DatosLaborales(
                id_solicitud=solicitud.id_solicitud,
                **datos_laborales,
            )
        )
        self.db.add(
            SolicitudContactoVivienda(
                id_solicitud=solicitud.id_solicitud,
                **contacto_vivienda,
            )
        )

        self.db.flush()
        return solicitud

    def obtener_ofertas(
        self,
        id_solicitud: uuid.UUID,
    ) -> list[OfertaCredito]:
        return (
            self.db.query(OfertaCredito)
            .filter(OfertaCredito.id_solicitud == id_solicitud)
            .all()
        )

    def obtener_oferta(
        self,
        id_solicitud: uuid.UUID,
        id_oferta: int,
    ) -> OfertaCredito | None:
        return (
            self.db.query(OfertaCredito)
            .filter(
                OfertaCredito.id_solicitud == id_solicitud,
                OfertaCredito.id_oferta == id_oferta,
            )
            .one_or_none()
        )

    def seleccionar_oferta(
        self,
        id_solicitud: uuid.UUID,
        id_oferta: int,
    ) -> OfertaCredito:
        oferta = self.obtener_oferta(id_solicitud, id_oferta)
        if oferta is None:
            raise ValueError(
                f"No existe la oferta {id_oferta} para la "
                f"solicitud {id_solicitud}"
            )
        if not oferta.elegible:
            raise ValueError(
                "No se puede seleccionar una oferta no elegible: "
                f"{oferta.motivo_no_elegible}"
            )

        # Desmarcar cualquier otra oferta seleccionada previamente
        # para esta solicitud (solo puede haber una activa a la vez).
        for otra in self.obtener_ofertas(id_solicitud):
            if otra.id_oferta != id_oferta and otra.seleccionada:
                otra.seleccionada = False

        oferta.seleccionada = True
        self.db.flush()
        return oferta
