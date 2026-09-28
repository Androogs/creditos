"""
Cálculo de INGRESO_FINAL según el BRD original, secciones 2.4.3 y
2.4.4.

Diferencia importante frente a la primera versión (basada en el
resumen automatizado): el BRD real NO hace una cadena de respaldo
automática "si A es 0, usar B, si B es 0, usar C" para Empleado/
Pensionado — si VALOR_INGRESO es 0 para esas ocupaciones, es
RECHAZO directo. El "ingreso declarado por el cliente" solo se usa
como disparador de una causal específica (no como fuente real de
ingreso): si VALOR_INGRESO=0 y QUANTO_3_MEDIO=0 pero el cliente sí
declaró ingresos mensuales, la causal es "Sin valor Ingreso y
Quanto" (es decir, se rechaza precisamente PORQUE no hay forma de
verificar lo que declaró).

AMBIGÜEDAD DETECTADA EN EL BRD (marcada, no resuelta en silencio):
el texto introductorio dice "para Empleado, Pensionado o Fuerzas
Militares se debe relacionar como Ingreso Final el valor de Valor
Ingreso", pero el bloque condicional que sigue solo cubre
"Empleado o Pensionado". Luego hay un bloque aparte:
"Si OCUPACION = Fuerzas Militares o Independiente & QUANTO_3_MEDIO>0
-> INGRESO_FINAL = QUANTO_3_MEDIO". Fuerzas Militares aparece en los
dos bloques con fuentes distintas. Aquí se implementa así: Fuerzas
Militares intenta primero Valor Ingreso (como el resto de
"Empleado/Pensionado/FFMM"), y si es 0, cae a Quanto (como dice el
segundo bloque) — es la lectura que concilia ambos fragmentos sin
descartar ninguno. Confirmar con quien mantiene el BRD.
"""

from dataclasses import dataclass

OCUPACION_INDEPENDIENTE = "independiente"
OCUPACION_FUERZAS_MILITARES = "fuerzas militares"
OCUPACIONES_VALOR_INGRESO = {"empleado", "pensionado", "fuerzas militares"}


@dataclass
class ResultadoIngresoFinal:
    ingreso_final: float
    fuente_usada: str  # "valor_ingreso" | "quanto3_medio" | "ninguna"
    rechazado: bool
    causal_codigo: str | None
    causal_descripcion: str | None


def calcular_ingreso_final(
    ocupacion: str,
    valor_ingreso: float | None,
    quanto3_medio: float | None,
    ingresos_mensuales_declarados: float | None,
) -> ResultadoIngresoFinal:

    ocupacion_normalizada = ocupacion.strip().lower()
    valor_ingreso = valor_ingreso or 0
    quanto3_medio = quanto3_medio or 0
    ingresos_mensuales_declarados = ingresos_mensuales_declarados or 0

    # Chequeo universal (BRD, aplica a todas las ocupaciones): si no
    # hay ni Valor Ingreso ni Quanto, pero sí hay un valor declarado
    # por el cliente (que NO se usa para el cálculo), se rechaza.
    if (
        valor_ingreso == 0
        and quanto3_medio == 0
        and ingresos_mensuales_declarados != 0
    ):
        return ResultadoIngresoFinal(
            ingreso_final=0,
            fuente_usada="ninguna",
            rechazado=True,
            causal_codigo="SIN_VALOR_INGRESO_Y_QUANTO",
            causal_descripcion="Sin valor Ingreso y Quanto",
        )

    if ocupacion_normalizada in ("empleado", "pensionado"):
        if valor_ingreso > 0:
            return ResultadoIngresoFinal(
                valor_ingreso, "valor_ingreso", False, None, None
            )
        return ResultadoIngresoFinal(
            0,
            "ninguna",
            True,
            "SIN_VALOR_INGRESO_Y_QUANTO",
            "Sin valor Ingreso y Quanto",
        )

    if ocupacion_normalizada == OCUPACION_FUERZAS_MILITARES:
        # Ver nota de ambigüedad en el docstring del módulo.
        if valor_ingreso > 0:
            return ResultadoIngresoFinal(
                valor_ingreso, "valor_ingreso", False, None, None
            )
        if quanto3_medio > 0:
            return ResultadoIngresoFinal(
                quanto3_medio, "quanto3_medio", False, None, None
            )
        return ResultadoIngresoFinal(
            0,
            "ninguna",
            True,
            "SIN_VALOR_INGRESO_Y_QUANTO",
            "Sin valor Ingreso y Quanto",
        )

    if ocupacion_normalizada == OCUPACION_INDEPENDIENTE:
        if quanto3_medio > 0:
            return ResultadoIngresoFinal(
                quanto3_medio, "quanto3_medio", False, None, None
            )
        return ResultadoIngresoFinal(
            0,
            "ninguna",
            True,
            "SIN_VALOR_INGRESO_Y_QUANTO",
            "Sin valor Ingreso y Quanto",
        )

    raise ValueError(
        f"Ocupación no reconocida para el cálculo de ingreso final: "
        f"'{ocupacion}'. Valores esperados: Empleado, Independiente, "
        f"Pensionado, Fuerzas Militares."
    )
