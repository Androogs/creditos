"""
Funciones financieras puras usadas por el motor de decisión y por
capacidad_pago_service.

IMPORTANTE — bug encontrado en el archivo de referencia
'Ejemplo Calculo cuotas 1.xlsx': la fórmula ahí escrita es

    = (Cupo * Tasa) / 1 - (1 / (1 + Tasa) ** Plazo)

que por precedencia de operadores en Excel hace "dividir entre 1" y
LUEGO restar, en vez de dividir por el paréntesis completo. Para un
cupo de 1.000, tasa 2%, plazo 36: esa fórmula da 19.5; el valor
correcto de la cuota (anualidad francesa estándar) es 39.23. Si esa
hoja se usa como referencia para programar, el gasto financiero
queda subestimado entre 25% y 50%, y la capacidad de pago sale
inflada.

Las funciones de este módulo implementan la fórmula correcta:

    cuota = monto * i / (1 - (1 + i) ** -n)
    valor_presente = cuota * (1 - (1 + i) ** -n) / i

donde i es la tasa periódica en decimal (ej. 2% -> 0.02) y n el
número de periodos.
"""


def cuota_anualidad(monto: float, tasa_pct: float, plazo_meses: int) -> float:
    """
    Cuota mensual de una anualidad francesa (cuota fija).
    tasa_pct: tasa mensual en porcentaje (ej. 2.0 para 2%).
    """
    if plazo_meses <= 0:
        raise ValueError("plazo_meses debe ser mayor que cero")

    i = tasa_pct / 100
    if i == 0:
        return monto / plazo_meses

    return monto * i / (1 - (1 + i) ** -plazo_meses)


def valor_presente_anualidad(
    cuota: float,
    tasa_pct: float,
    plazo_meses: int,
) -> float:
    """
    Valor presente (cupo/monto financiable) de una serie de cuotas
    iguales. Es la inversa de cuota_anualidad: dado lo que la
    capacidad de pago puede cubrir mensualmente, calcula el monto
    máximo financiable.
    """
    if plazo_meses <= 0:
        raise ValueError("plazo_meses debe ser mayor que cero")

    i = tasa_pct / 100
    if i == 0:
        return cuota * plazo_meses

    return cuota * (1 - (1 + i) ** -plazo_meses) / i


_MESES_POR_PERIODICIDAD = {
    "mensual": 1,
    "bimensual": 2,
    "trimestral": 3,
    "semestral": 6,
    "anual": 12,
}


def cuota_a_valor_mensual(cuota: float, periodicidad: str) -> float:
    """
    Convierte una cuota reportada en el buró (mensual, bimensual,
    trimestral, semestral o anual, según Tabla 7 - Modalidad de
    Pago del manual HDC) a su equivalente mensual, dividiendo entre
    el número de meses del periodo.
    """
    periodicidad_normalizada = periodicidad.strip().lower()
    meses = _MESES_POR_PERIODICIDAD.get(periodicidad_normalizada)

    if meses is None:
        raise ValueError(
            f"Periodicidad no reconocida: '{periodicidad}'. "
            f"Valores esperados: {list(_MESES_POR_PERIODICIDAD)}"
        )

    return cuota / meses
