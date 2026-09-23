import uuid
from types import SimpleNamespace

import pytest

from backend.services.elegibilidad_service import EligibilidadService


def _regla(campo, operador, valor_json):
    return SimpleNamespace(
        campo=campo, operador=operador, valor_json=valor_json
    )


def _producto(id_aliado_producto, reglas):
    return SimpleNamespace(
        id_aliado_producto=id_aliado_producto, reglas=reglas
    )


@pytest.mark.asyncio
async def test_producto_elegible_cuando_cumple_todas_las_reglas():
    service = EligibilidadService(db=None)
    producto = _producto(
        1,
        [
            _regla("score", ">=", 650),
            _regla("edad", "<=", 65),
        ],
    )

    oferta = await service.evaluar_producto(
        id_solicitud=uuid.uuid4(),
        producto=producto,
        datos_solicitud={"score": 720, "edad": 34},
    )

    assert oferta.elegible is True
    assert oferta.motivo_no_elegible is None


@pytest.mark.asyncio
async def test_producto_no_elegible_reporta_motivo():
    service = EligibilidadService(db=None)
    producto = _producto(
        1,
        [
            _regla("score", ">=", 650),
        ],
    )

    oferta = await service.evaluar_producto(
        id_solicitud=uuid.uuid4(),
        producto=producto,
        datos_solicitud={"score": 500},
    )

    assert oferta.elegible is False
    assert "score" in oferta.motivo_no_elegible


@pytest.mark.asyncio
async def test_operador_in_funciona_con_listas():
    service = EligibilidadService(db=None)
    producto = _producto(
        1,
        [
            _regla("tipo_contrato", "IN", ["indefinido", "fijo"]),
        ],
    )

    oferta = await service.evaluar_producto(
        id_solicitud=uuid.uuid4(),
        producto=producto,
        datos_solicitud={"tipo_contrato": "obra_labor"},
    )

    assert oferta.elegible is False
