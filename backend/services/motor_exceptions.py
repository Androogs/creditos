class ReglaNoDefinidaError(Exception):
    """
    Se lanza cuando el motor de decisión llega a un punto donde
    necesita una fórmula, ponderación o punto de corte que aún no
    ha sido definido por negocio (pendiente de los manuales del
    motor propio).

    Usar esta excepción en vez de NotImplementedError directo
    permite que error_middleware.py devuelva un 501 explícito en
    vez de un 500 genérico, dejando claro en la respuesta HTTP que
    es una regla de negocio pendiente y no un bug.
    """

    def __init__(self, detalle: str) -> None:
        super().__init__(detalle)
