from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ClienteInput(BaseModel):
    tipo_documento: str
    num_cedula: str
    nombre_completo: str
    fecha_nacimiento: date
    ocupacion: str | None = None
    nacionalidad: str = "Colombia"


class DatosLaboralesInput(BaseModel):
    tipo_contrato: str | None = None
    meses_continuidad: int | None = None
    ingreso_mensual: float | None = None
    otros_ingresos: float = 0


class ContactoViviendaInput(BaseModel):
    estrato: int | None = None
    personas_a_cargo: int | None = None
    tipo_vivienda: str | None = None


class CrearSolicitudRequest(BaseModel):
    cliente: ClienteInput
    datos_laborales: DatosLaboralesInput
    contacto_vivienda: ContactoViviendaInput
    moneda: str = "COP"


class CrearSolicitudResponse(BaseModel):
    id_solicitud: UUID
    num_solicitud: int
    estado: str


class SeleccionarOfertaRequest(BaseModel):
    id_oferta: int
