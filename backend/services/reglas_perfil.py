"""
Perfil de score, perfil de ingreso y matriz de decisión, según el
BRD ORIGINAL (BRD-Prefiltro_Cliente_InversionesPacifico_22012026.docx,
secciones 2.4.5, 2.4.6 y 2.4.7).

Diferencia importante frente a la primera versión de este archivo
(basada en un resumen automatizado, no en el documento real): la
matriz de decisión NO tiene "Estudio" ni "Requiere codeudor" — todo
resultado es APROBADO o RECHAZADO. El texto final del BRD sí
menciona de pasada "Todo lo que no quede en Rechazado, Estudio o
Requiere codeudor será Aprobado", pero ninguna tabla del documento
llega a producir esos dos estados intermedios, así que no se
implementan aquí (posible texto heredado de una versión anterior de
la estrategia).
"""

from dataclasses import dataclass

from backend.services.motor_parametros import MotorParametros

PerfilScore = str  # "A" | "B" | "C" | "D" | "RECHAZO_PUNTO_CORTE" | "RECHAZO_SIN_EXPERIENCIA"
PerfilIngreso = str  # "ALTO" | "MEDIO" | "BAJO" | "GRIS" | "RECHAZO"
Decision = str  # "APROBADO" | "RECHAZADO"


@dataclass
class ResultadoDecisionParcial:
    decision: Decision
    causal_codigo: str | None
    causal_descripcion: str | None


def perfil_score_empleado_pensionado_ffmm(
    score: float,
    params: MotorParametros,
) -> PerfilScore:
    if score < params.score_piso_experiencia:
        return "RECHAZO_SIN_EXPERIENCIA"
    if score < params.score_ep_4:
        return "RECHAZO_PUNTO_CORTE"
    if score >= params.score_ep_1:
        return "A"
    if score >= params.score_ep_2:
        return "B"
    if score >= params.score_ep_3:
        return "C"
    return "D"


def perfil_score_independiente(
    score: float,
    params: MotorParametros,
) -> PerfilScore:
    if score < params.score_piso_experiencia:
        return "RECHAZO_SIN_EXPERIENCIA"
    if score < params.score_if_4:
        return "RECHAZO_PUNTO_CORTE"
    if score >= params.score_if_1:
        return "A"
    if score >= params.score_if_2:
        return "B"
    if score >= params.score_if_3:
        return "C"
    return "D"


def perfil_score(
    ocupacion: str,
    score: float,
    params: MotorParametros,
) -> PerfilScore:
    ocupacion_normalizada = ocupacion.strip().lower()

    # NOTA: el BRD agrupa "Empleado o Pensionado" para la escalera
    # de score con cortes 750/680/600/500, pero la matriz de
    # decisión posterior agrupa "Pensionado o Fuerzas Militares"
    # (no "Empleado o Fuerzas Militares"). Es decir, Fuerzas
    # Militares usa la escalera de SCORE de Independiente (770/700/
    # 620/520) pero la MATRIZ de decisión de Pensionado. Esto es lo
    # que el documento dice literalmente en cada sección; no es un
    # error de esta implementación.
    if ocupacion_normalizada in ("independiente", "fuerzas militares"):
        return perfil_score_independiente(score, params)
    if ocupacion_normalizada in ("empleado", "pensionado"):
        return perfil_score_empleado_pensionado_ffmm(score, params)

    raise ValueError(f"Ocupación no reconocida: '{ocupacion}'")


def perfil_ingreso_empleado(
    ingreso_final_smmlv: float,
    tipo_contrato: str,
    meses_continuidad: int | None,
    params: MotorParametros,
) -> PerfilIngreso:
    tipo_contrato_normalizado = (tipo_contrato or "").strip().lower()
    meses_continuidad = meses_continuidad or 0

    if tipo_contrato_normalizado == "indefinido":
        cumple_continuidad = (
            meses_continuidad >= params.meses_continuidad_indefinido
        )
    elif tipo_contrato_normalizado in ("fijo", "obra o labor", "obra labor"):
        cumple_continuidad = (
            meses_continuidad >= params.meses_continuidad_fijo_o_labor
        )
    else:
        # TIPO CONTRATO = NA u otro valor no cubierto por el BRD:
        # no hay regla explícita, se trata como "no cumple
        # continuidad" (cae a GRIS si el ingreso alcanza, o a
        # Rechazo si no alcanza ni el piso).
        cumple_continuidad = False

    if ingreso_final_smmlv < params.ingreso_e_bajo:
        return "RECHAZO"

    if not cumple_continuidad:
        return "GRIS"

    if ingreso_final_smmlv >= params.ingreso_e_alto:
        return "ALTO"
    if ingreso_final_smmlv >= params.ingreso_e_medio:
        return "MEDIO"
    return "BAJO"


def perfil_ingreso_pensionado_ffmm(
    ingreso_final_smmlv: float,
    params: MotorParametros,
) -> PerfilIngreso:
    if ingreso_final_smmlv >= params.ingreso_pf_alto:
        return "ALTO"
    if ingreso_final_smmlv >= params.ingreso_pf_medio:
        return "MEDIO"
    if ingreso_final_smmlv >= params.ingreso_pf_bajo:
        return "BAJO"
    return "RECHAZO"


def perfil_ingreso_independiente(
    ingreso_final_smmlv: float,
    anios_camara_comercio: float | None,
    params: MotorParametros,
) -> PerfilIngreso:
    anios = anios_camara_comercio or 0

    if (
        ingreso_final_smmlv >= params.ingreso_i_alto
        and anios >= params.anios_cam_alto
    ):
        return "ALTO"
    if (
        params.ingreso_i_medio_min <= ingreso_final_smmlv < params.ingreso_i_alto
        and anios >= params.anios_cam_medio
    ):
        return "MEDIO"
    if (
        params.ingreso_i_bajo_min
        <= ingreso_final_smmlv
        < params.ingreso_i_medio_min
        and anios >= params.anios_cam_bajo
    ):
        return "BAJO"
    if (
        params.ingreso_i_gris_min
        < ingreso_final_smmlv
        < params.ingreso_i_gris_max
        and anios >= params.anios_cam_gris
    ):
        return "GRIS"
    if ingreso_final_smmlv <= params.ingreso_i_piso_rechazo:
        return "RECHAZO"

    # Zona sin regla explícita en el BRD (ej. ingreso entre 1.6 y
    # 2.0 pero años cámara insuficientes para "BAJO", y tampoco cae
    # en ningún otro rango): se trata como Rechazo por vacío de
    # política, coherente con la cláusula del BRD "los registros que
    # no apliquen a las casuísticas anteriores... quedan Rechazado
    # con causal 'No cumple política interna'".
    return "SIN_REGLA"


def perfil_ingreso(
    ocupacion: str,
    ingreso_final_smmlv: float,
    tipo_contrato: str | None,
    meses_continuidad: int | None,
    anios_camara_comercio: float | None,
    params: MotorParametros,
) -> PerfilIngreso:
    ocupacion_normalizada = ocupacion.strip().lower()

    if ocupacion_normalizada == "empleado":
        return perfil_ingreso_empleado(
            ingreso_final_smmlv,
            tipo_contrato or "",
            meses_continuidad,
            params,
        )
    if ocupacion_normalizada in ("pensionado", "fuerzas militares"):
        return perfil_ingreso_pensionado_ffmm(ingreso_final_smmlv, params)
    if ocupacion_normalizada == "independiente":
        return perfil_ingreso_independiente(
            ingreso_final_smmlv, anios_camara_comercio, params
        )

    raise ValueError(f"Ocupación no reconocida: '{ocupacion}'")


# --- Matrices de decisión (BRD sección 2.4.7), literal por ocupación ---

def decidir_empleado(
    perfil_score_valor: PerfilScore,
    perfil_ingreso_valor: PerfilIngreso,
) -> ResultadoDecisionParcial:
    if perfil_score_valor == "RECHAZO_PUNTO_CORTE":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_SCORE_CORTE", "Score por debajo del punto de corte"
        )
    if perfil_score_valor == "RECHAZO_SIN_EXPERIENCIA":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_SIN_EXPERIENCIA", "Cliente sin experiencia crediticia"
        )
    if perfil_ingreso_valor == "RECHAZO":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_INGRESOS_PERMITIDO", "Ingresos por debajo del permitido"
        )
    if perfil_score_valor == "D":
        return ResultadoDecisionParcial(
            "RECHAZADO", "D_NO_CUMPLE_SCORE", "No Cumple Score"
        )
    if perfil_ingreso_valor == "GRIS":
        return ResultadoDecisionParcial(
            "RECHAZADO", "GRIS_NO_CONTINUIDAD", "No Cumple Continuidad"
        )
    if perfil_ingreso_valor in ("ALTO", "MEDIO", "BAJO"):
        return ResultadoDecisionParcial("APROBADO", None, None)

    return ResultadoDecisionParcial(
        "RECHAZADO", "SIN_POLITICA", "No cumple política interna"
    )


def decidir_pensionado_ffmm(
    perfil_score_valor: PerfilScore,
    perfil_ingreso_valor: PerfilIngreso,
) -> ResultadoDecisionParcial:
    if perfil_score_valor == "RECHAZO_PUNTO_CORTE":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_SCORE_CORTE", "Score por debajo del punto de corte"
        )
    if perfil_score_valor == "RECHAZO_SIN_EXPERIENCIA":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_SIN_EXPERIENCIA", "Cliente sin experiencia crediticia"
        )
    if perfil_ingreso_valor == "RECHAZO":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_INGRESOS_PERMITIDO", "Ingresos por debajo del permitido"
        )
    if perfil_score_valor == "D":
        return ResultadoDecisionParcial(
            "RECHAZADO", "D_NO_CUMPLE_SCORE", "No Cumple Score"
        )
    if perfil_ingreso_valor == "BAJO":
        return ResultadoDecisionParcial(
            "RECHAZADO", "BAJO_NO_INGRESOS", "No Cumple Ingresos"
        )
    if perfil_ingreso_valor == "GRIS":
        return ResultadoDecisionParcial(
            "RECHAZADO", "GRIS_NO_CONTINUIDAD", "No Cumple Continuidad"
        )
    if perfil_ingreso_valor in ("ALTO", "MEDIO"):
        return ResultadoDecisionParcial("APROBADO", None, None)

    return ResultadoDecisionParcial(
        "RECHAZADO", "SIN_POLITICA", "No cumple política interna"
    )


def decidir_independiente(
    perfil_score_valor: PerfilScore,
    perfil_ingreso_valor: PerfilIngreso,
) -> ResultadoDecisionParcial:
    if perfil_score_valor == "RECHAZO_PUNTO_CORTE":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_SCORE_CORTE", "Score por debajo del punto de corte"
        )
    if perfil_score_valor == "RECHAZO_SIN_EXPERIENCIA":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_SIN_EXPERIENCIA", "Cliente sin experiencia crediticia"
        )
    if perfil_ingreso_valor == "RECHAZO":
        return ResultadoDecisionParcial(
            "RECHAZADO", "R_INGRESOS_PERMITIDO", "Ingresos por debajo del permitido"
        )
    if perfil_score_valor == "D":
        return ResultadoDecisionParcial(
            "RECHAZADO", "D_NO_CUMPLE_SCORE", "No Cumple Score"
        )
    if perfil_ingreso_valor == "BAJO":
        return ResultadoDecisionParcial(
            "RECHAZADO", "BAJO_NO_INGRESOS", "No Cumple Ingresos"
        )
    if perfil_ingreso_valor == "GRIS":
        return ResultadoDecisionParcial(
            "RECHAZADO", "GRIS_NO_CAMARA", "No Cumple Registro Cámara"
        )
    if perfil_ingreso_valor in ("ALTO", "MEDIO"):
        return ResultadoDecisionParcial("APROBADO", None, None)

    return ResultadoDecisionParcial(
        "RECHAZADO", "SIN_POLITICA", "No cumple política interna"
    )


def decidir_por_ocupacion(
    ocupacion: str,
    perfil_score_valor: PerfilScore,
    perfil_ingreso_valor: PerfilIngreso,
) -> ResultadoDecisionParcial:
    ocupacion_normalizada = ocupacion.strip().lower()

    if ocupacion_normalizada == "empleado":
        return decidir_empleado(perfil_score_valor, perfil_ingreso_valor)
    if ocupacion_normalizada in ("pensionado", "fuerzas militares"):
        return decidir_pensionado_ffmm(perfil_score_valor, perfil_ingreso_valor)
    if ocupacion_normalizada == "independiente":
        return decidir_independiente(perfil_score_valor, perfil_ingreso_valor)

    raise ValueError(f"Ocupación no reconocida: '{ocupacion}'")
