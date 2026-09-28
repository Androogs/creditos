"""
Filtros duros de rechazo, según el BRD original, sección
"Validaciones Decisión Rechazado" (política de edad/nacionalidad/
RUNT + tabla de 11 políticas de buró) y "Exclusiones Acierta".

Total: 14 causales de la tabla principal (11 de buró + edad +
nacionalidad + RUNT), más "Mora 30 días vigentes" que el BRD marca
aparte con la nota "Antes era Estudio" (es decir, en esta versión
del BRD ya es Rechazo, no Estudio), y las 5 causales de exclusión de
score (Acierta).
"""

from dataclasses import dataclass

from backend.services.motor_parametros import MotorParametros


@dataclass
class CausalDisparada:
    codigo: str
    descripcion: str


@dataclass
class DatosBuroParaFiltros:
    # --- Política previa a la tabla (edad/nacionalidad/RUNT) ---
    edad: int | None = None
    nacionalidad_colombiana: bool = True
    tiene_multas_runt: bool = False

    # --- Tabla de 11 políticas de buró ---
    embargos_vigentes: bool = False
    cancelacion_mal_manejo: bool = False  # novedad 03
    cartera_castigada: bool = False
    dudoso_recaudo: bool = False
    mora_60_o_mas_vigente: bool = False
    mora_30_historica_veces: int = 0  # umbral >= 2 (params.umbral_mora_30_historica)
    mora_60_historica: bool = False   # umbral >= 1
    mora_90_historica: bool = False   # umbral >= 1
    calificacion: str | None = None   # 'A'..'K'; C/D/E/K -> rechazo
    reestructuraciones: int = 0       # umbral >= 2
    documento_vigente: bool = True
    documento_es_cedula_extranjeria: bool = False  # excepción código 25

    # --- Mora 30 vigentes (sección aparte del BRD, "Antes era Estudio") ---
    mora_30_vigente: bool = False

    # --- Exclusiones Acierta (score) ---
    es_persona_natural: bool = True
    exclusion_tipo5_sin_obligaciones: bool = False
    exclusion_tipo1_sin_desempeno: bool = False
    reportado_fallecido: bool = False
    exclusion_solo_codeudor: bool = False


_CALIFICACIONES_RECHAZO = {"C", "D", "E", "K"}


def evaluar_filtros_duros(
    datos: DatosBuroParaFiltros,
    params: MotorParametros,
) -> list[CausalDisparada]:
    causales: list[CausalDisparada] = []

    # --- Exclusiones Acierta (van primero: el BRD dice que si hay
    # causal de rechazo activa no se continúa con validaciones que
    # implican consumo adicional) ---
    if not datos.es_persona_natural:
        causales.append(
            CausalDisparada(
                "EXCL_PJ", "Clientes diferentes a Persona Natural"
            )
        )
    if datos.exclusion_tipo5_sin_obligaciones:
        causales.append(
            CausalDisparada(
                "EXCL_TIPO5",
                "Cliente no ha tenido obligaciones del pasivo y/o el activo",
            )
        )
    if datos.exclusion_tipo1_sin_desempeno:
        causales.append(
            CausalDisparada(
                "EXCL_TIPO1",
                "Cliente sin información financiera en cuentas del activo",
            )
        )
    if datos.reportado_fallecido:
        causales.append(
            CausalDisparada(
                "EXCL_FALLECIDO", "Clientes reportados como fallecidos"
            )
        )
    if datos.exclusion_solo_codeudor:
        causales.append(
            CausalDisparada(
                "EXCL_CODEUDOR", "Clientes que solo tienen cuentas como codeudor"
            )
        )

    # --- Política de edad / nacionalidad / RUNT ---
    if datos.edad is None or not (
        params.edad_minima <= datos.edad <= params.edad_maxima
    ):
        causales.append(
            CausalDisparada("POL_EDAD", "No Cumple Politica de Edad")
        )
    if not datos.nacionalidad_colombiana:
        causales.append(
            CausalDisparada(
                "POL_NACIONALIDAD", "Nacionalidad Diferente a Colombiana"
            )
        )
    if datos.tiene_multas_runt:
        causales.append(
            CausalDisparada("POL_RUNT", "Multas en el RUNT")
        )

    # --- Tabla de 11 políticas de buró ---
    if datos.embargos_vigentes:
        causales.append(CausalDisparada("POL1", "Embargos vigentes"))
    if datos.cancelacion_mal_manejo:
        causales.append(CausalDisparada("POL2", "Cancelaciones por mal habito"))
    if datos.cartera_castigada:
        causales.append(CausalDisparada("POL3", "Cartera Castigada"))
    if datos.dudoso_recaudo:
        causales.append(CausalDisparada("POL4", "Dudoso Recaudo"))
    if datos.mora_60_o_mas_vigente:
        causales.append(
            CausalDisparada("POL5", "Mora 60 días o más vigentes")
        )
    if datos.mora_30_historica_veces >= params.umbral_mora_30_historica:
        causales.append(CausalDisparada("POL6", "Mora histórica 30 días"))
    if datos.mora_60_historica:
        causales.append(CausalDisparada("POL7", "Mora histórica 60 días"))
    if datos.mora_90_historica:
        causales.append(
            CausalDisparada("POL8", "Mora histórica 90 días o más")
        )
    if datos.calificacion and datos.calificacion.upper() in _CALIFICACIONES_RECHAZO:
        causales.append(
            CausalDisparada("POL9", "Calificación diferente A y B")
        )
    if datos.reestructuraciones >= params.umbral_reestructuraciones:
        causales.append(CausalDisparada("POL10", "Reestructuración"))
    if not datos.documento_vigente and not datos.documento_es_cedula_extranjeria:
        causales.append(CausalDisparada("POL11", "Documento no vigente"))

    # --- Mora 30 vigentes (antes Estudio, ahora Rechazo) ---
    if datos.mora_30_vigente:
        causales.append(
            CausalDisparada("MORA30_VIGENTE", "Mora 30 días vigentes")
        )

    return causales
