"""
Modelos SQLAlchemy (Fase 1) que mapean las tablas de database/schema.sql
necesarias para el motor de decisión propio.

Alcance: se mapean las tablas que el motor de decisión, el cálculo
de capacidad de pago y el motor de elegibilidad necesitan leer o
escribir directamente. El resto de tablas del esquema (seguros,
desembolsos, bancos, auditoría, etc.) no se mapean aquí porque no
son parte del flujo de evaluación de crédito en sí; se pueden ir
agregando en este mismo archivo o en módulos adicionales bajo
db_models/ a medida que se necesiten.

No se reimplementan aquí los ENUM de Postgres uno por uno: se usan
como String con el valor validado a nivel de aplicación, para no
duplicar el CREATE TYPE de schema.sql. Si se prefiere el mapeo
estricto a ENUM de Postgres, reemplazar String por
sqlalchemy.dialects.postgresql.ENUM apuntando al tipo ya creado en
la base de datos (create_type=False).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db_models.base import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id_cliente: Mapped[int] = mapped_column(primary_key=True)
    tipo_documento: Mapped[str] = mapped_column(String(30))
    num_cedula: Mapped[str] = mapped_column(String(40), unique=True)
    nombre_completo: Mapped[str] = mapped_column(String(200))
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    ocupacion: Mapped[str | None] = mapped_column(String(30))
    es_persona_natural: Mapped[bool] = mapped_column(Boolean, default=True)
    nacionalidad: Mapped[str] = mapped_column(String(80), default="Colombia")

    solicitudes: Mapped[list["SolicitudCredito"]] = relationship(
        back_populates="cliente"
    )


class SolicitudCredito(Base):
    __tablename__ = "solicitud_credito"

    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True
    )
    num_solicitud: Mapped[int] = mapped_column(unique=True)
    id_cliente: Mapped[int] = mapped_column(ForeignKey("cliente.id_cliente"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    moneda: Mapped[str] = mapped_column(String(3), default="COP")
    decision: Mapped[str | None] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(30), default="creada")
    descripcion_estado: Mapped[str | None] = mapped_column(Text)

    cliente: Mapped["Cliente"] = relationship(back_populates="solicitudes")
    datos_laborales: Mapped["DatosLaborales"] = relationship(
        back_populates="solicitud", uselist=False
    )
    contacto_vivienda: Mapped["SolicitudContactoVivienda"] = relationship(
        back_populates="solicitud", uselist=False
    )
    cotizantes: Mapped[list["Cotizante"]] = relationship(
        back_populates="solicitud"
    )
    evaluaciones: Mapped[list["EvaluacionCredito"]] = relationship(
        back_populates="solicitud"
    )
    capacidades_pago: Mapped[list["CapacidadPago"]] = relationship(
        back_populates="solicitud"
    )
    causales: Mapped[list["SolicitudCausal"]] = relationship(
        back_populates="solicitud"
    )
    ofertas: Mapped[list["OfertaCredito"]] = relationship(
        back_populates="solicitud"
    )


class DatosLaborales(Base):
    __tablename__ = "datos_laborales"

    id_datos_laborales: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("solicitud_credito.id_solicitud"),
        unique=True,
    )
    tipo_contrato: Mapped[str | None] = mapped_column(String(20))
    meses_continuidad: Mapped[int | None] = mapped_column(Integer)
    ingreso_mensual: Mapped[float | None] = mapped_column(Numeric(18, 2))
    otros_ingresos: Mapped[float] = mapped_column(Numeric(18, 2), default=0)

    # Agregado al implementar el motor propio: solo aplica para
    # Independientes (perfil de ingreso, ver reglas_perfil.py).
    anios_camara_comercio: Mapped[float | None] = mapped_column(Numeric(6, 2))

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="datos_laborales"
    )


class SolicitudContactoVivienda(Base):
    __tablename__ = "solicitud_contacto_vivienda"

    id_contacto_vivienda: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("solicitud_credito.id_solicitud"),
        unique=True,
    )
    estrato: Mapped[int | None] = mapped_column(SmallInteger)
    personas_a_cargo: Mapped[int | None] = mapped_column(SmallInteger)
    tipo_vivienda: Mapped[str | None] = mapped_column(String(50))

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="contacto_vivienda"
    )


class Cotizante(Base):
    __tablename__ = "cotizante"

    id_cotizante: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("solicitud_credito.id_solicitud")
    )
    razon_social_aportante: Mapped[str] = mapped_column(String(200))
    valor_ingreso: Mapped[float | None] = mapped_column(Numeric(18, 2))
    promedio_ultimos_3_meses: Mapped[float | None] = mapped_column(
        Numeric(18, 2)
    )
    mediana: Mapped[float | None] = mapped_column(Numeric(18, 2))
    moda: Mapped[float | None] = mapped_column(Numeric(18, 2))
    tendencia: Mapped[str | None] = mapped_column(String(40))
    percentil: Mapped[float | None] = mapped_column(Numeric(8, 4))
    meses_continuidad: Mapped[int | None] = mapped_column(Integer)

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="cotizantes"
    )
    ingresos_mensuales: Mapped[list["CotizanteIngresoMensual"]] = relationship(
        back_populates="cotizante"
    )


class CotizanteIngresoMensual(Base):
    __tablename__ = "cotizante_ingreso_mensual"

    id_cotizante: Mapped[int] = mapped_column(
        ForeignKey("cotizante.id_cotizante"), primary_key=True
    )
    periodo: Mapped[date] = mapped_column(Date, primary_key=True)
    ingreso: Mapped[float] = mapped_column(Numeric(18, 2))

    cotizante: Mapped["Cotizante"] = relationship(
        back_populates="ingresos_mensuales"
    )


class CriterioEvaluacion(Base):
    __tablename__ = "criterio_evaluacion"

    id_criterio: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))  # 'buro' | 'interno' | 'aliado'


class EvaluacionCredito(Base):
    __tablename__ = "evaluacion_credito"

    id_evaluacion: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("solicitud_credito.id_solicitud")
    )
    version: Mapped[int] = mapped_column(SmallInteger, default=1)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)
    origen_evaluacion: Mapped[str] = mapped_column(
        String(40), default="motor_pacifico"
    )
    score: Mapped[float | None] = mapped_column(Numeric(8, 2))
    valor_ingreso: Mapped[float | None] = mapped_column(Numeric(18, 2))
    ingreso_final: Mapped[float | None] = mapped_column(Numeric(18, 2))
    endeudamiento: Mapped[float | None] = mapped_column(Numeric(8, 4))
    capacidad_pago: Mapped[float | None] = mapped_column(Numeric(18, 2))

    # Variables de riesgo hoy provistas por Datacrédito (tipo 'buro'
    # en criterio_evaluacion). Se mantienen en el modelo porque la
    # tabla ya existe así en schema.sql; de dónde se llenan estos
    # valores es la decisión de negocio pendiente (ver reporte,
    # sección "Riesgos y puntos por definir").
    mora_historica_90: Mapped[int] = mapped_column(Integer, default=0)
    mora_historica_60: Mapped[int] = mapped_column(Integer, default=0)
    mora_historica_30: Mapped[int] = mapped_column(Integer, default=0)
    mora_60: Mapped[int] = mapped_column(Integer, default=0)
    mora_30: Mapped[int] = mapped_column(Integer, default=0)
    embargo: Mapped[int] = mapped_column(Integer, default=0)
    dudoso_recaudo: Mapped[int] = mapped_column(Integer, default=0)
    cartera_castigada: Mapped[int] = mapped_column(Integer, default=0)
    cancelaciones_negativas: Mapped[int] = mapped_column(Integer, default=0)
    obligaciones_reestructuradas: Mapped[int] = mapped_column(
        Integer, default=0
    )
    calificacion_diferente_ab: Mapped[int] = mapped_column(
        Integer, default=0
    )
    documento_vigente: Mapped[bool | None] = mapped_column(Boolean)

    # Agregados al implementar el motor propio (BRD-IMPL-111350):
    # letra de calificación real (A, B, C, D, E, AA, BB, CC, K),
    # necesaria para el filtro duro CAUSAL_R10; quanto3_medio, usado
    # en la cadena de respaldo de ingreso final; reportado_fallecido
    # para CAUSAL_R1; y el código de exclusión del score (0/4/99/
    # 70-77) que cambia la lógica de decisión.
    calificacion: Mapped[str | None] = mapped_column(String(5))
    quanto3_medio: Mapped[float | None] = mapped_column(Numeric(18, 2))
    reportado_fallecido: Mapped[bool] = mapped_column(Boolean, default=False)
    score_codigo_exclusion: Mapped[str | None] = mapped_column(String(5))

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="evaluaciones"
    )
    detalles: Mapped[list["EvaluacionDetalle"]] = relationship(
        back_populates="evaluacion"
    )


class EvaluacionDetalle(Base):
    __tablename__ = "evaluacion_detalle"

    id_evaluacion_detalle: Mapped[int] = mapped_column(primary_key=True)
    id_evaluacion: Mapped[int] = mapped_column(
        ForeignKey("evaluacion_credito.id_evaluacion")
    )
    id_criterio: Mapped[int] = mapped_column(
        ForeignKey("criterio_evaluacion.id_criterio")
    )
    resultado: Mapped[bool] = mapped_column(Boolean)
    puntaje: Mapped[float | None] = mapped_column(Numeric(8, 2))
    causal: Mapped[str | None] = mapped_column(Text)

    evaluacion: Mapped["EvaluacionCredito"] = relationship(
        back_populates="detalles"
    )
    criterio: Mapped["CriterioEvaluacion"] = relationship()


class SolicitudCausal(Base):
    __tablename__ = "solicitud_causal"

    id_solicitud_causal: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("solicitud_credito.id_solicitud")
    )
    id_criterio: Mapped[int | None] = mapped_column(
        ForeignKey("criterio_evaluacion.id_criterio")
    )
    codigo: Mapped[str] = mapped_column(String(60))
    descripcion: Mapped[str] = mapped_column(Text)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="causales"
    )


class CapacidadPago(Base):
    __tablename__ = "capacidad_pago"

    id_capacidad: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("solicitud_credito.id_solicitud")
    )
    version: Mapped[int] = mapped_column(SmallInteger, default=1)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True)
    salario_minimo: Mapped[float | None] = mapped_column(Numeric(18, 2))
    ingreso_final: Mapped[float | None] = mapped_column(Numeric(18, 2))
    ingreso_final_smlmv: Mapped[float | None] = mapped_column(Numeric(8, 4))
    gastos_personales: Mapped[float | None] = mapped_column(Numeric(18, 2))
    disponible_1: Mapped[float | None] = mapped_column(Numeric(18, 2))
    capacidad_pago_2: Mapped[float | None] = mapped_column(Numeric(18, 2))
    tasa_cupo: Mapped[float | None] = mapped_column(Numeric(8, 4))
    plazo_cupo: Mapped[int | None] = mapped_column(Integer)
    cupo_calculado: Mapped[float | None] = mapped_column(Numeric(18, 2))
    cupo_aprobado: Mapped[float | None] = mapped_column(Numeric(18, 2))

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="capacidades_pago"
    )


class AliadoProducto(Base):
    __tablename__ = "aliado_producto"

    id_aliado_producto: Mapped[int] = mapped_column(primary_key=True)
    id_aliado: Mapped[int] = mapped_column(
        ForeignKey("aliado_financiero.id_aliado")
    )
    nombre: Mapped[str] = mapped_column(String(180))
    tasa_min: Mapped[float | None] = mapped_column(Numeric(8, 4))
    tasa_max: Mapped[float | None] = mapped_column(Numeric(8, 4))
    monto_min: Mapped[float | None] = mapped_column(Numeric(18, 2))
    monto_max: Mapped[float | None] = mapped_column(Numeric(18, 2))
    score_min: Mapped[int | None] = mapped_column(SmallInteger)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    reglas: Mapped[list["AliadoReglaElegibilidad"]] = relationship(
        back_populates="producto"
    )
    ofertas: Mapped[list["OfertaCredito"]] = relationship(
        back_populates="producto"
    )


class AliadoFinanciero(Base):
    __tablename__ = "aliado_financiero"

    id_aliado: Mapped[int] = mapped_column(primary_key=True)
    nit: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(180), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    es_propio: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class AliadoReglaElegibilidad(Base):
    __tablename__ = "aliado_regla_elegibilidad"

    id_regla: Mapped[int] = mapped_column(primary_key=True)
    id_aliado_producto: Mapped[int] = mapped_column(
        ForeignKey("aliado_producto.id_aliado_producto")
    )
    campo: Mapped[str] = mapped_column(String(80))
    operador: Mapped[str] = mapped_column(String(10))
    valor_json: Mapped[dict] = mapped_column(JSONB)

    producto: Mapped["AliadoProducto"] = relationship(back_populates="reglas")


class OfertaCredito(Base):
    __tablename__ = "oferta_credito"

    id_oferta: Mapped[int] = mapped_column(primary_key=True)
    id_solicitud: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("solicitud_credito.id_solicitud")
    )
    id_aliado_producto: Mapped[int] = mapped_column(
        ForeignKey("aliado_producto.id_aliado_producto")
    )
    elegible: Mapped[bool] = mapped_column(Boolean)
    motivo_no_elegible: Mapped[str | None] = mapped_column(Text)
    tasa_ofrecida: Mapped[float | None] = mapped_column(Numeric(8, 4))
    plazo_ofrecido: Mapped[int | None] = mapped_column(Integer)
    cuota_mensual: Mapped[float | None] = mapped_column(Numeric(18, 2))
    monto_aprobado: Mapped[float | None] = mapped_column(Numeric(18, 2))
    seleccionada: Mapped[bool] = mapped_column(Boolean, default=False)

    solicitud: Mapped["SolicitudCredito"] = relationship(
        back_populates="ofertas"
    )
    producto: Mapped["AliadoProducto"] = relationship(
        back_populates="ofertas"
    )
