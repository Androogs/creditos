"""
Script de prueba manual del motor de decisión, usando un HC y un VI
reales de Experian en formato JSON.

Corre solo la lógica de negocio pura (sin base de datos):

1. Filtros duros
2. Ingreso final
3. Perfil de score
4. Perfil de ingreso
5. Matriz de decisión
6. Capacidad de pago
7. Cuota de la moto

IMPORTANTE:
La prueba NO solicita una ocupación manualmente.

La categoría del cliente se obtiene de DATOS_CLIENTE mediante
_determinar_categoria_cliente().

En producción, DATOS_CLIENTE debe reemplazarse por los datos que
ya vienen de la solicitud/formulario.

Si los datos disponibles no permiten determinar la categoría,
el motor detiene la prueba con un error explícito en lugar de
inventar una ocupación.

CÓMO USARLO:

1. Coloca:
       HC_APROBADO.json
       VI_APROBADO.json

   en la misma carpeta de este archivo.

2. Ajusta:
       _extraer_datos_hc()
       _extraer_quanto3_medio()
       _extraer_score()
       _extraer_valor_ingreso()
       _extraer_ingreso_declarado()

   contra la estructura REAL de tus JSON.

3. Ajusta DATOS_CLIENTE con los datos reales que en producción
   vienen de la solicitud.

4. Ejecuta el archivo desde VS Code con F5/F9.

5. Revisa:
       - filtros
       - ingreso final
       - perfil score
       - perfil ingreso
       - matriz
       - capacidad
       - cuota
       - decisión final
"""

import json
import sys
from pathlib import Path


# ---------------------------------------------------------------
# 0. RAÍZ DEL PROYECTO
# ---------------------------------------------------------------

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)


# ---------------------------------------------------------------
# IMPORTS DEL MOTOR
# ---------------------------------------------------------------

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

from backend.services.reglas_ingreso import (
    calcular_ingreso_final,
)

from backend.services.reglas_perfil import (
    decidir_por_ocupacion,
    perfil_ingreso,
    perfil_score,
)


# ===============================================================
# 1. ARCHIVOS JSON
# ===============================================================

RUTA_HC = Path(__file__).parent / "HC_APROBADO.json"
RUTA_VI = Path(__file__).parent / "VI_APROBADO.json"


def cargar_json(ruta: Path) -> dict:
    """
    Carga un JSON y valida que exista.
    """

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el archivo requerido: {ruta}"
        )

    try:
        return json.loads(
            ruta.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"El archivo no contiene un JSON válido: {ruta}"
        ) from exc


hc = cargar_json(RUTA_HC)
vi = cargar_json(RUTA_VI)


# ===============================================================
# 2. DATOS DEL CLIENTE
# ===============================================================
#
# Estos NO son una pregunta para el usuario.
#
# En producción estos datos deberían venir de la solicitud/formulario
# ya diligenciado.
#
# Para esta prueba manual puedes modificar los valores.
#
# La diferencia importante es que NO existe:
#
#     OCUPACION = "Empleado"
#
# El motor determina automáticamente la categoría mediante
# _determinar_categoria_cliente().
# ===============================================================

DATOS_CLIENTE = {
    # -----------------------------------------------------------
    # Datos laborales
    # -----------------------------------------------------------

    # Si tiene una relación laboral con contrato, el motor puede
    # clasificarlo como empleado.
    "tipo_contrato": "Indefinido",

    # Tiempo de continuidad laboral.
    "meses_continuidad": None,

    # Si tiene información de Cámara de Comercio, puede utilizarse
    # para identificar la rama de independiente.
    #
    # None = no aplica / no disponible.
    "anios_camara_comercio": None,

    # Estas banderas deben venir de la solicitud/formulario
    # cuando correspondan.
    "es_pensionado": False,
    "es_fuerzas_militares": False,

    # -----------------------------------------------------------
    # Datos generales
    # -----------------------------------------------------------

    "edad": 32,

    # Nacionalidad.
    "nacionalidad_colombiana": True,

    # -----------------------------------------------------------
    # Datos de la solicitud
    # -----------------------------------------------------------

    "salario_minimo": 1_423_500,

    "tasa_credito_pct": 2.2,

    "plazo_meses": 36,

    "monto_moto_solicitado": 8_000_000,
}


# ===============================================================
# 3. DETERMINACIÓN AUTOMÁTICA DE CATEGORÍA
# ===============================================================

def _determinar_categoria_cliente(
    datos_cliente: dict,
) -> str:
    """
    Determina la categoría que utilizarán las reglas_perfil.py.

    NO pregunta la ocupación.

    Utiliza exclusivamente datos que ya forman parte del cliente /
    solicitud.

    Retorna uno de:

        Empleado
        Independiente
        Pensionado
        Fuerzas Militares

    Si los datos son insuficientes, lanza un error explícito.

    IMPORTANTE:
    Ajusta esta función a los campos reales de tu solicitud.
    """

    es_fuerzas_militares = bool(
        datos_cliente.get("es_fuerzas_militares")
    )

    es_pensionado = bool(
        datos_cliente.get("es_pensionado")
    )

    tipo_contrato = (
        datos_cliente.get("tipo_contrato") or ""
    ).strip().lower()

    anios_camara = datos_cliente.get(
        "anios_camara_comercio"
    )

    # -----------------------------------------------------------
    # 1. Fuerzas Militares
    # -----------------------------------------------------------

    if es_fuerzas_militares:
        return "Fuerzas Militares"

    # -----------------------------------------------------------
    # 2. Pensionado
    # -----------------------------------------------------------

    if es_pensionado:
        return "Pensionado"

    # -----------------------------------------------------------
    # 3. Empleado
    # -----------------------------------------------------------

    if tipo_contrato in (
        "indefinido",
        "fijo",
        "obra o labor",
        "obra labor",
    ):
        return "Empleado"

    # -----------------------------------------------------------
    # 4. Independiente
    # -----------------------------------------------------------

    if anios_camara is not None:
        return "Independiente"

    # -----------------------------------------------------------
    # No fue posible determinar la categoría
    # -----------------------------------------------------------

    raise ValueError(
        "No fue posible determinar automáticamente la categoría "
        "del cliente.\n\n"
        "Datos disponibles:\n"
        f"  tipo_contrato: {datos_cliente.get('tipo_contrato')!r}\n"
        f"  es_pensionado: {datos_cliente.get('es_pensionado')!r}\n"
        f"  es_fuerzas_militares: "
        f"{datos_cliente.get('es_fuerzas_militares')!r}\n"
        f"  anios_camara_comercio: "
        f"{datos_cliente.get('anios_camara_comercio')!r}\n\n"
        "Revisa los datos de la solicitud o ajusta "
        "_determinar_categoria_cliente()."
    )


# ===============================================================
# 4. EXTRAER DATOS DEL HC PARA FILTROS DUROS
# ===============================================================

def _extraer_datos_hc(
    hc: dict,
) -> DatosBuroParaFiltros:
    """
    Extrae del HC los datos necesarios para filtros duros.

    IMPORTANTE:
    Los paths son provisionales porque la estructura real del HC
    no fue proporcionada aquí.

    Ajusta esta función contra el JSON real de Experian.
    """

    calificacion = None

    embargos_vigentes = False
    cartera_castigada = False
    dudoso_recaudo = False
    mora_60_o_mas_vigente = False

    mora_30_historica_veces = 0
    mora_60_historica = False
    mora_90_historica = False

    reestructuraciones = 0

    documento_vigente = True
    reportado_fallecido = False

    # -----------------------------------------------------------
    # TODO:
    #
    # Reemplazar con el recorrido REAL del HC.
    #
    # Ejemplo:
    #
    # for cuenta in (
    #     hc.get("endeudamientoActual", {})
    #        .get("cuentas", [])
    # ):
    #
    #     if cuenta.get("moraDias", 0) >= 60:
    #         mora_60_o_mas_vigente = True
    #
    # -----------------------------------------------------------

    print(
        "ADVERTENCIA HC: _extraer_datos_hc() "
        "usa valores provisionales."
    )

    return DatosBuroParaFiltros(
        edad=DATOS_CLIENTE["edad"],
        nacionalidad_colombiana=DATOS_CLIENTE[
            "nacionalidad_colombiana"
        ],
        tiene_multas_runt=False,
        embargos_vigentes=embargos_vigentes,
        cancelacion_mal_manejo=False,
        cartera_castigada=cartera_castigada,
        dudoso_recaudo=dudoso_recaudo,
        mora_60_o_mas_vigente=mora_60_o_mas_vigente,
        mora_30_historica_veces=mora_30_historica_veces,
        mora_60_historica=mora_60_historica,
        mora_90_historica=mora_90_historica,
        calificacion=calificacion,
        reestructuraciones=reestructuraciones,
        documento_vigente=documento_vigente,
        reportado_fallecido=reportado_fallecido,
    )


# ===============================================================
# 5. EXTRAER QUANTO
# ===============================================================

def _extraer_quanto3_medio(
    hc: dict,
) -> float:
    """
    Extrae Quanto Medio.

    Según el Anexo Quanto:
        producto = "62"
        valor1 = Quanto Medio
        valor1 viene en miles de pesos.

    Por eso:
        valor1 * 1000

    Ajustar el recorrido contra el HC real.
    """

    # -----------------------------------------------------------
    # TODO:
    #
    # Ejemplo aproximado:
    #
    # for producto in hc.get("productosValores", []):
    #     if str(producto.get("producto")) == "62":
    #         valor1 = producto.get("valor1")
    #
    #         if valor1 is None:
    #             return 0.0
    #
    #         return float(valor1) * 1000
    # -----------------------------------------------------------

    print(
        "ADVERTENCIA HC: _extraer_quanto3_medio() "
        "usa 0.0 provisionalmente."
    )

    return 0.0


# ===============================================================
# 6. EXTRAER SCORE
# ===============================================================

def _extraer_score(
    hc: dict,
) -> float:
    """
    Extrae el Score Advance.

    Según la documentación, el código esperado es Z0.

    Ajustar el path contra el HC real.
    """

    # -----------------------------------------------------------
    # TODO:
    #
    # Ejemplo:
    #
    # for producto in hc.get("productosValores", []):
    #     if producto.get("codigo") == "Z0":
    #         return float(producto["valor1"])
    # -----------------------------------------------------------

    print(
        "ADVERTENCIA HC: _extraer_score() "
        "usa 0.0 provisionalmente."
    )

    return 0.0


# ===============================================================
# 7. EXTRAER INGRESO DEL VI
# ===============================================================

def _extraer_valor_ingreso(
    vi: dict,
) -> float:
    """
    Extrae VALOR_INGRESO del VI.

    Regla:
        suma de los promedios de los aportantes
        de los últimos 3 meses.

    Ajustar el path contra el JSON real.
    """

    # -----------------------------------------------------------
    # TODO:
    #
    # Ejemplo:
    #
    # total = 0.0
    #
    # for aportante in vi.get("aportantes", []):
    #     promedio = aportante.get(
    #         "promedio_ult_tres_meses"
    #     )
    #
    #     if promedio is not None:
    #         total += float(promedio)
    #
    # return total
    # -----------------------------------------------------------

    print(
        "ADVERTENCIA VI: _extraer_valor_ingreso() "
        "usa 0.0 provisionalmente."
    )

    return 0.0


# ===============================================================
# 8. INGRESO DECLARADO
# ===============================================================

def _extraer_ingreso_declarado(
    vi: dict,
) -> float:
    """
    El BRD utiliza este valor únicamente para evaluar la causal
    relacionada con ausencia de VALOR_INGRESO y QUANTO.

    No se utiliza como ingreso principal cuando existe una fuente
    válida de ingreso.
    """

    # TODO:
    # Ajustar al campo real de la solicitud / VI.

    return 0.0


# ===============================================================
# 9. MAIN
# ===============================================================

def main() -> None:

    print("=" * 70)
    print("PRUEBA MANUAL DEL MOTOR DE DECISIÓN")
    print("=" * 70)

    params = MotorParametros()

    # -----------------------------------------------------------
    # Determinar automáticamente la categoría
    # -----------------------------------------------------------

    categoria_cliente = _determinar_categoria_cliente(
        DATOS_CLIENTE
    )

    print("\n=== CATEGORÍA DEL CLIENTE ===")
    print(f"  Categoría determinada: {categoria_cliente}")

    # -----------------------------------------------------------
    # Variables de solicitud
    # -----------------------------------------------------------

    salario_minimo = DATOS_CLIENTE[
        "salario_minimo"
    ]

    tasa_credito_pct = DATOS_CLIENTE[
        "tasa_credito_pct"
    ]

    plazo_meses = DATOS_CLIENTE[
        "plazo_meses"
    ]

    monto_moto_solicitado = DATOS_CLIENTE[
        "monto_moto_solicitado"
    ]

    tipo_contrato = DATOS_CLIENTE.get(
        "tipo_contrato"
    )

    meses_continuidad = DATOS_CLIENTE.get(
        "meses_continuidad"
    )

    anios_camara_comercio = DATOS_CLIENTE.get(
        "anios_camara_comercio"
    )

    # ===========================================================
    # PASO 1: FILTROS DUROS
    # ===========================================================

    datos_buro = _extraer_datos_hc(hc)

    causales_duras = evaluar_filtros_duros(
        datos_buro,
        params,
    )

    print("\n=== FILTROS DUROS ===")

    if causales_duras:

        for causal in causales_duras:
            print(
                f"  [{causal.codigo}] "
                f"{causal.descripcion}"
            )

        print(
            "\nDECISIÓN FINAL: RECHAZADO "
            "(filtro duro)"
        )

        return

    print("  Ninguna causal disparada.")

    # ===========================================================
    # PASO 2: INGRESO FINAL
    # ===========================================================

    valor_ingreso = _extraer_valor_ingreso(vi)

    quanto3_medio = _extraer_quanto3_medio(hc)

    ingreso_declarado = _extraer_ingreso_declarado(
        vi
    )

    resultado_ingreso = calcular_ingreso_final(
        ocupacion=categoria_cliente,
        valor_ingreso=valor_ingreso,
        quanto3_medio=quanto3_medio,
        ingresos_mensuales_declarados=ingreso_declarado,
    )

    print("\n=== INGRESO FINAL ===")

    print(
        f"  VALOR_INGRESO: "
        f"{valor_ingreso:,.0f}"
    )

    print(
        f"  QUANTO_3_MEDIO: "
        f"{quanto3_medio:,.0f}"
    )

    print(
        f"  INGRESO_FINAL: "
        f"{resultado_ingreso.ingreso_final:,.0f}"
        f" "
        f"(fuente: "
        f"{resultado_ingreso.fuente_usada})"
    )

    if resultado_ingreso.rechazado:

        print(
            f"\n  [{resultado_ingreso.causal_codigo}] "
            f"{resultado_ingreso.causal_descripcion}"
        )

        print(
            "\nDECISIÓN FINAL: RECHAZADO"
        )

        return

    # -----------------------------------------------------------
    # Conversión a SMMLV
    # -----------------------------------------------------------

    ingreso_final_smmlv = (
        resultado_ingreso.ingreso_final
        / salario_minimo
    )

    print(
        f"  INGRESO_FINAL_SMMLV: "
        f"{ingreso_final_smmlv:.2f}"
    )

    # ===========================================================
    # PASO 3: PERFIL DE SCORE
    # ===========================================================

    score = _extraer_score(hc)

    perfil_score_valor = perfil_score(
        categoria_cliente,
        score,
        params,
    )

    # ===========================================================
    # PASO 3B: PERFIL DE INGRESO
    # ===========================================================

    perfil_ingreso_valor = perfil_ingreso(
        ocupacion=categoria_cliente,
        ingreso_final_smmlv=ingreso_final_smmlv,
        tipo_contrato=tipo_contrato,
        meses_continuidad=meses_continuidad,
        anios_camara_comercio=anios_camara_comercio,
        params=params,
    )

    # ===========================================================
    # PASO 3C: MATRIZ
    # ===========================================================

    resultado_matriz = decidir_por_ocupacion(
        categoria_cliente,
        perfil_score_valor,
        perfil_ingreso_valor,
    )

    print("\n=== PERFIL Y MATRIZ ===")

    print(
        f"  CATEGORÍA: "
        f"{categoria_cliente}"
    )

    print(
        f"  SCORE: "
        f"{score}"
    )

    print(
        f"  PERFIL_SCORE: "
        f"{perfil_score_valor}"
    )

    print(
        f"  PERFIL_INGRESO: "
        f"{perfil_ingreso_valor}"
    )

    print(
        f"  DECISIÓN MATRIZ: "
        f"{resultado_matriz.decision}"
        + (
            f"  "
            f"[{resultado_matriz.causal_codigo}] "
            f"{resultado_matriz.causal_descripcion}"
            if resultado_matriz.causal_codigo
            else ""
        )
    )

    if resultado_matriz.decision == "RECHAZADO":

        print(
            "\nDECISIÓN FINAL: RECHAZADO"
        )

        return

    # ===========================================================
    # PASO 4: CAPACIDAD DE PAGO
    # ===========================================================

    resultado_capacidad = calcular_capacidad_pago(
        ingreso_final=resultado_ingreso.ingreso_final,
        ingreso_final_smmlv=ingreso_final_smmlv,
        gasto_financiero_no_rotativo=0,
        gasto_financiero_rotativo=0,
        params=params,
    )

    print("\n=== CAPACIDAD DE PAGO ===")

    print(
        f"  Gastos personales: "
        f"{resultado_capacidad.gastos_personales:,.0f}"
    )

    print(
        f"  Endeudamiento: "
        f"{resultado_capacidad.endeudamiento_pct:.1f}%"
    )

    if resultado_capacidad.rechazado:

        print(
            f"  [{resultado_capacidad.causal_codigo}] "
            f"{resultado_capacidad.causal_descripcion}"
        )

        print(
            "\nDECISIÓN FINAL: RECHAZADO"
        )

        return

    print(
        f"  Disponible: "
        f"{resultado_capacidad.disponible:,.0f}"
    )

    print(
        f"  Capacidad de pago: "
        f"{resultado_capacidad.capacidad_de_pago:,.0f}"
    )

    print(
        f"  Cupo sugerido: "
        f"{resultado_capacidad.cupo_sugerido:,.0f}"
    )

    # ===========================================================
    # PASO 5: CUOTA DE LA MOTO
    # ===========================================================

    cuota_sugerida = calcular_cuota_sugerida(
        resultado_capacidad.cupo_sugerido,
        tasa_credito_pct,
        plazo_meses,
    )

    cuota_moto = calcular_cuota_sugerida(
        monto_moto_solicitado,
        tasa_credito_pct,
        plazo_meses,
    )

    aprueba, codigo, descripcion = (
        validar_capacidad_para_moto(
            cuota_moto,
            cuota_sugerida,
        )
    )

    print("\n=== CUOTA MOTO ===")

    print(
        f"  Cuota sugerida según cupo: "
        f"{cuota_sugerida:,.0f}"
    )

    print(
        f"  Cuota moto solicitada: "
        f"{cuota_moto:,.0f}"
    )

    if not aprueba:

        print(
            f"  [{codigo}] "
            f"{descripcion}"
        )

        print(
            "\nDECISIÓN FINAL: RECHAZADO"
        )

        return

    # ===========================================================
    # DECISIÓN FINAL
    # ===========================================================

    print("\n" + "=" * 70)
    print("DECISIÓN FINAL: APROBADO")
    print("=" * 70)


# ===============================================================
# EJECUCIÓN
# ===============================================================

if __name__ == "__main__":
    main()
