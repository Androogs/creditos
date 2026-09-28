"""
Motor de decisión propio de Inversiones Pacíficas, según el BRD
original: BRD-Prefiltro_Cliente_InversionesPacifico_22012026.docx.

Flujo (BRD: "Lineal" — se evalúan todas las condiciones aplicables y
se devuelven todas las causales que disparen, pero el resultado
final es siempre binario: APROBADO o RECHAZADO):

    1. Filtros duros (exclusiones de score + política de edad/
       nacionalidad/RUNT + tabla de 11 políticas de buró + mora 30
       vigentes). Si dispara alguno -> RECHAZADO, y el BRD indica
       explícitamente NO seguir con validaciones de consumo
       adicional (valor ingreso), así que se corta aquí.
    2. Ingreso final (reglas_ingreso) -> si es RECHAZO, se corta.
    3. Perfil de score y perfil de ingreso, según ocupación
       (reglas_perfil) -> matriz de decisión por ocupación.
    4. Si lo anterior no rechazó: capacidad de pago (gastos
       personales, endeudamiento, disponible, capacidad, cupo
       sugerido) -> puede rechazar por endeudamiento/sin disponible/
       sin capacidad.
    5. Validación de la cuota de la moto solicitada contra la cuota
       que permite el cupo sugerido.

Los parámetros (MotorParametros) ya traen los valores reales del
BRD por default — no hace falta configurarlos externamente salvo
que el BRD cambie de versión.
"""

import datetime
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.repositories.evaluacion_repository import (
    EvaluacionRepository,
)
from backend.repositories.solicitud_repository import (
    SolicitudRepository,
)
from backend.services.capacidad_pago_service import (
    calcular_capacidad_pago,
    calcular_cuota_sugerida,
    validar_capacidad_para_moto,
)
from backend.services.motor_parametros import MotorParametros
from backend.services.reglas_filtros_duros import (
    DatosBuroParaFiltros,
    evaluar_filtros_duros,
)
from backend.services.reglas_ingreso import calcular_ingreso_final
from backend.services.reglas_perfil import (
    decidir_por_ocupacion,
    perfil_ingreso,
    perfil_score,
)
from backend.utils.loggers import get_logger


logger = get_logger("motor_decision.propio")


@dataclass
class CausalMotor:
    codigo: str
    descripcion: str


def _calcular_edad(fecha_nacimiento, hoy) -> int:
    return (
        hoy.year
        - fecha_nacimiento.year
        - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    )


class MotorDecisionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.solicitud_repo = SolicitudRepository(db)
        self.evaluacion_repo = EvaluacionRepository(db)

    async def evaluar(self, payload: dict) -> dict:
        id_solicitud = uuid.UUID(str(payload["id_solicitud"]))

        logger.info(
            "Evaluación motor propio solicitada",
            extra={"id_solicitud": str(id_solicitud)},
        )

        solicitud = self.solicitud_repo.obtener_con_datos_para_evaluar(
            id_solicitud
        )
        if solicitud is None:
            raise ValueError(f"No existe la solicitud {id_solicitud}")
        if solicitud.cliente is None:
            raise ValueError(f"La solicitud {id_solicitud} no tiene cliente")
        if solicitud.datos_laborales is None:
            raise ValueError(
                f"La solicitud {id_solicitud} no tiene datos_laborales"
            )

        params = MotorParametros()
        ocupacion = solicitud.cliente.ocupacion
        if not ocupacion:
            raise ValueError(
                f"El cliente de la solicitud {id_solicitud} no tiene "
                f"ocupación registrada."
            )

        causales: list[CausalMotor] = []

        # --- Paso 1: filtros duros ---
        datos_buro_raw = payload.get("datos_buro", {})
        datos_buro = DatosBuroParaFiltros(
            edad=_calcular_edad(
                solicitud.cliente.fecha_nacimiento, datetime.date.today()
            ),
            nacionalidad_colombiana=datos_buro_raw.get(
                "nacionalidad_colombiana", True
            ),
            tiene_multas_runt=datos_buro_raw.get("tiene_multas_runt", False),
            embargos_vigentes=datos_buro_raw.get("embargos_vigentes", False),
            cancelacion_mal_manejo=datos_buro_raw.get(
                "cancelacion_mal_manejo", False
            ),
            cartera_castigada=datos_buro_raw.get("cartera_castigada", False),
            dudoso_recaudo=datos_buro_raw.get("dudoso_recaudo", False),
            mora_60_o_mas_vigente=datos_buro_raw.get(
                "mora_60_o_mas_vigente", False
            ),
            mora_30_historica_veces=datos_buro_raw.get(
                "mora_30_historica_veces", 0
            ),
            mora_60_historica=datos_buro_raw.get("mora_60_historica", False),
            mora_90_historica=datos_buro_raw.get("mora_90_historica", False),
            calificacion=datos_buro_raw.get("calificacion"),
            reestructuraciones=datos_buro_raw.get("reestructuraciones", 0),
            documento_vigente=datos_buro_raw.get("documento_vigente", True),
            documento_es_cedula_extranjeria=datos_buro_raw.get(
                "documento_es_cedula_extranjeria", False
            ),
            mora_30_vigente=datos_buro_raw.get("mora_30_vigente", False),
            es_persona_natural=datos_buro_raw.get("es_persona_natural", True),
            exclusion_tipo5_sin_obligaciones=datos_buro_raw.get(
                "exclusion_tipo5_sin_obligaciones", False
            ),
            exclusion_tipo1_sin_desempeno=datos_buro_raw.get(
                "exclusion_tipo1_sin_desempeno", False
            ),
            reportado_fallecido=datos_buro_raw.get(
                "reportado_fallecido", False
            ),
            exclusion_solo_codeudor=datos_buro_raw.get(
                "exclusion_solo_codeudor", False
            ),
        )

        filtros_disparados = evaluar_filtros_duros(datos_buro, params)
        for c in filtros_disparados:
            causales.append(CausalMotor(c.codigo, c.descripcion))

        if causales:
            # BRD: si hay causal de rechazo activa, no continuar con
            # validaciones de consumo adicional (valor ingreso).
            return self._guardar_y_responder(
                id_solicitud, "RECHAZADO", causales, score=None
            )

        # --- Paso 2: ingreso final ---
        score = float(payload["score"])
        quanto3_medio = payload.get("quanto3_medio")
        salario_minimo = float(payload["salario_minimo"])

        valor_ingreso_actual = None
        if solicitud.evaluaciones:
            valor_ingreso_actual = solicitud.evaluaciones[-1].valor_ingreso

        resultado_ingreso = calcular_ingreso_final(
            ocupacion=ocupacion,
            valor_ingreso=(
                float(valor_ingreso_actual) if valor_ingreso_actual else None
            ),
            quanto3_medio=quanto3_medio,
            ingresos_mensuales_declarados=(
                float(solicitud.datos_laborales.ingreso_mensual)
                if solicitud.datos_laborales.ingreso_mensual
                else None
            ),
        )

        if resultado_ingreso.rechazado:
            causales.append(
                CausalMotor(
                    resultado_ingreso.causal_codigo,
                    resultado_ingreso.causal_descripcion,
                )
            )
            return self._guardar_y_responder(
                id_solicitud,
                "RECHAZADO",
                causales,
                score=score,
                ingreso_final=resultado_ingreso.ingreso_final,
            )

        ingreso_final_smmlv = (
            resultado_ingreso.ingreso_final / salario_minimo
            if salario_minimo > 0
            else 0
        )

        # --- Paso 3: perfil de score / ingreso y matriz ---
        perfil_score_valor = perfil_score(ocupacion, score, params)
        perfil_ingreso_valor = perfil_ingreso(
            ocupacion=ocupacion,
            ingreso_final_smmlv=ingreso_final_smmlv,
            tipo_contrato=solicitud.datos_laborales.tipo_contrato,
            meses_continuidad=solicitud.datos_laborales.meses_continuidad,
            anios_camara_comercio=(
                solicitud.datos_laborales.anios_camara_comercio
            ),
            params=params,
        )
        resultado_matriz = decidir_por_ocupacion(
            ocupacion, perfil_score_valor, perfil_ingreso_valor
        )
        if resultado_matriz.causal_codigo:
            causales.append(
                CausalMotor(
                    resultado_matriz.causal_codigo,
                    resultado_matriz.causal_descripcion,
                )
            )

        if resultado_matriz.decision == "RECHAZADO":
            return self._guardar_y_responder(
                id_solicitud,
                "RECHAZADO",
                causales,
                score=score,
                ingreso_final=resultado_ingreso.ingreso_final,
                perfil_score_valor=perfil_score_valor,
                perfil_ingreso_valor=perfil_ingreso_valor,
            )

        # --- Paso 4: capacidad de pago (aplica siempre, BRD 2.4.8) ---
        resultado_capacidad = calcular_capacidad_pago(
            ingreso_final=resultado_ingreso.ingreso_final,
            ingreso_final_smmlv=ingreso_final_smmlv,
            gasto_financiero_no_rotativo=float(
                payload.get("gasto_financiero_no_rotativo", 0)
            ),
            gasto_financiero_rotativo=float(
                payload.get("gasto_financiero_rotativo", 0)
            ),
            params=params,
        )
        if resultado_capacidad.rechazado:
            causales.append(
                CausalMotor(
                    resultado_capacidad.causal_codigo,
                    resultado_capacidad.causal_descripcion,
                )
            )
            return self._guardar_y_responder(
                id_solicitud,
                "RECHAZADO",
                causales,
                score=score,
                ingreso_final=resultado_ingreso.ingreso_final,
                perfil_score_valor=perfil_score_valor,
                perfil_ingreso_valor=perfil_ingreso_valor,
                resultado_capacidad=resultado_capacidad,
            )

        # --- Paso 5: cuota de la moto vs. cuota que permite el cupo ---
        cuota_sugerida = calcular_cuota_sugerida(
            resultado_capacidad.cupo_sugerido,
            float(payload["tasa_credito_pct"]),
            int(payload["plazo_meses"]),
        )
        cuota_moto = calcular_cuota_sugerida(
            float(payload["monto_moto_solicitado"]),
            float(payload["tasa_credito_pct"]),
            int(payload["plazo_meses"]),
        )
        aprueba_moto, causal_codigo, causal_desc = validar_capacidad_para_moto(
            cuota_moto, cuota_sugerida
        )
        decision_final = "APROBADO"
        if not aprueba_moto:
            causales.append(CausalMotor(causal_codigo, causal_desc))
            decision_final = "RECHAZADO"

        return self._guardar_y_responder(
            id_solicitud,
            decision_final,
            causales,
            score=score,
            ingreso_final=resultado_ingreso.ingreso_final,
            perfil_score_valor=perfil_score_valor,
            perfil_ingreso_valor=perfil_ingreso_valor,
            resultado_capacidad=resultado_capacidad,
            cuota_sugerida=cuota_sugerida,
            cuota_moto=cuota_moto,
        )

    def _guardar_y_responder(
        self,
        id_solicitud: uuid.UUID,
        decision: str,
        causales: list[CausalMotor],
        score: float | None,
        ingreso_final: float | None = None,
        perfil_score_valor: str | None = None,
        perfil_ingreso_valor: str | None = None,
        resultado_capacidad=None,
        cuota_sugerida: float | None = None,
        cuota_moto: float | None = None,
    ) -> dict:

        evaluacion = self.evaluacion_repo.crear_evaluacion(
            id_solicitud=id_solicitud,
            score=score,
            detalles=[],
            endeudamiento=(
                resultado_capacidad.endeudamiento_pct
                if resultado_capacidad
                else None
            ),
            capacidad_pago=(
                resultado_capacidad.capacidad_de_pago
                if resultado_capacidad
                else None
            ),
            ingreso_final=ingreso_final,
        )
        self.solicitud_repo.actualizar_decision(
            id_solicitud=id_solicitud, decision=decision
        )

        return {
            "id_solicitud": str(id_solicitud),
            "id_evaluacion": evaluacion.id_evaluacion,
            "version": evaluacion.version,
            "score": score,
            "perfil_score": perfil_score_valor,
            "perfil_ingreso": perfil_ingreso_valor,
            "ingreso_final": ingreso_final,
            "endeudamiento_pct": (
                resultado_capacidad.endeudamiento_pct
                if resultado_capacidad
                else None
            ),
            "capacidad_de_pago": (
                resultado_capacidad.capacidad_de_pago
                if resultado_capacidad
                else None
            ),
            "cupo_sugerido": (
                resultado_capacidad.cupo_sugerido
                if resultado_capacidad
                else None
            ),
            "cuota_sugerida": cuota_sugerida,
            "cuota_moto": cuota_moto,
            "decision": decision,
            "causales": [
                {"codigo": c.codigo, "descripcion": c.descripcion}
                for c in causales
            ],
        }
