from typing import Any

from pydantic import BaseModel, Field


class InquiryKeyValue(BaseModel):
    key: str
    value: str


class InquiryParameter(BaseModel):
    paramType: str
    keyvalue: InquiryKeyValue


class PreselectaRequest(BaseModel):
    idNumber: str
    idType: str
    firstLastName: str | None = None

    inquiryClientId: str
    inquiryClientType: str

    inquiryUserId: str
    inquiryUserType: str

    inquiryParameters: list[InquiryParameter]


class ValorIngresoRequest(BaseModel):
    TipoIdentificacionUsuario: str
    IdentificacionUsuario: str

    TipoIDSuscriptor: str
    NitSuscriptor: str
    NombreSuscriptor: str

    TipoIdBuscar: str
    IdentificacionBuscar: str

    IngresoValidar: str
    ProductoId: str
    CanalConsulta: str
    ProductoConsulta: str