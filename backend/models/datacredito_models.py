from pydantic import BaseModel


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
    NombreSuscriptor: str

    TipoIdBuscar: str
    IdentificacionBuscar: str

    IngresoValidar: str
    ProductoID: str
    CanalConsultas: str
    ProductoConsultas: str