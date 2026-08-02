"""Un `Infinity` o `NaN` en el cuerpo debe rechazarse, no tumbar el endpoint.

Los routers traducen la peticion con `Decimal(str(campo))`. `Decimal("inf")` se
construye sin error, pero `quantize()` sobre un valor no finito levanta
`decimal.InvalidOperation`, que ningun router captura. Las clases de dominio son
objetos de Python planos, no modelos Pydantic, asi que tampoco lo rechazan.

Habia ademas un segundo fallo encadenado: aunque la validacion si rechazara el
valor, FastAPI devuelve la entrada recibida dentro del cuerpo del error, y
`json.dumps` no admite `inf`. El 422 correcto se convertia en un 500 al
serializar el propio mensaje de error.

Los cuerpos van como texto crudo a proposito: `Infinity` y `NaN` son literales
que el modulo `json` de Python emite y acepta, pero el cliente HTTP de las
pruebas se niega a codificarlos. Un cliente cualquiera si puede enviarlos, que
es justo lo que hay que cubrir.
"""

import pytest

JSON = {"Content-Type": "application/json"}

# Cada caso: (ruta, cuerpo JSON crudo con un no-finito, campo que debe senalarse)
CASOS_NO_FINITOS = [
    pytest.param(
        "/api/v1/salud/gmm/calcular",
        '{"edad":40,"sexo":"masculino","suma_asegurada":Infinity,"deducible":20000,"coaseguro_pct":0.1}',
        "suma_asegurada",
        id="gmm-suma-asegurada",
    ),
    pytest.param(
        "/api/v1/danos/auto/calcular",
        '{"valor_vehiculo":Infinity,"tipo_vehiculo":"sedan_mediano",'
        '"antiguedad_anos":2,"zona":"CDMX","edad_conductor":35}',
        "valor_vehiculo",
        id="auto-valor-vehiculo",
    ),
    pytest.param(
        "/api/v1/reserves/chain-ladder",
        '{"triangle":[[Infinity,200],[150]],"origin_years":[2021,2022]}',
        "triangle",
        id="chain-ladder-triangulo",
    ),
    pytest.param(
        "/api/v1/danos/frecuencia-severidad",
        '{"dist_frecuencia":"poisson","params_frecuencia":{"lambda_":Infinity},'
        '"dist_severidad":"exponencial","params_severidad":{"lambda_":1},'
        '"n_simulaciones":1000}',
        "params_frecuencia",
        id="frecuencia-severidad-lambda",
    ),
    pytest.param(
        "/api/v1/reserves/chain-ladder",
        '{"triangle":[[NaN,200],[150]],"origin_years":[2021,2022]}',
        "triangle",
        id="chain-ladder-nan",
    ),
]


@pytest.mark.parametrize(("ruta", "cuerpo", "campo"), CASOS_NO_FINITOS)
def test_no_finito_se_rechaza_con_422(api_client, ruta, cuerpo, campo):
    """422 senalando el campo, no 500."""
    respuesta = api_client.post(ruta, content=cuerpo, headers=JSON)

    assert respuesta.status_code == 422, respuesta.text
    detalle = respuesta.json()["detail"]
    assert any(campo in [str(p) for p in err["loc"]] for err in detalle), detalle


def test_el_cuerpo_del_error_es_json_valido(api_client):
    """El detalle debe serializarse aunque la entrada rechazada fuera `inf`.

    Es el fallo encadenado: el rechazo era correcto y aun asi devolvia 500
    porque `json.dumps` no admite `inf` al reflejar la entrada.
    """
    respuesta = api_client.post(
        "/api/v1/danos/auto/calcular",
        content='{"valor_vehiculo":Infinity,"tipo_vehiculo":"sedan_mediano",'
        '"antiguedad_anos":2,"zona":"CDMX","edad_conductor":35}',
        headers=JSON,
    )
    assert respuesta.status_code == 422
    # No debe levantar: el cuerpo es JSON valido y el valor viaja como texto.
    detalle = respuesta.json()["detail"]
    assert detalle[0]["input"] == "inf"


def test_una_peticion_finita_sigue_pasando(api_client):
    """El filtro no debe estorbar el uso normal."""
    respuesta = api_client.post(
        "/api/v1/danos/auto/calcular",
        json={
            "valor_vehiculo": 350000,
            "tipo_vehiculo": "sedan_mediano",
            "antiguedad_anos": 2,
            "zona": "cdmx_sur",
            "edad_conductor": 35,
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["prima_total"] > 0
