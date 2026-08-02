"""Ayuda compartida para las regresiones de sexo heredado en el API.

Hasta la unificacion, `/api/v1/pricing/*` y `/api/v1/pensiones/*` codificaban el
sexo como "H"/"M" (hombre/mujer) y `/api/v1/salud/*` como "M"/"F"
(masculino/femenino). El mismo caracter "M" significaba cosas opuestas segun el
endpoint. Si alguna de las tres letras volviera a ser aceptada, un cliente viejo
podria cambiar de sexo sin enterarse.

Cada router tiene una prueba que usa estas funciones para exigir dos cosas:
que las tres letras devuelvan 422, y que el cuerpo del error nombre el conjunto
valido en vez de limitarse a decir que el valor es invalido.
"""

from typing import Any

#: Las tres iniciales que circularon por el API antes de la unificacion.
LETRAS_HEREDADAS = ["H", "M", "F"]


def assert_rechaza_sexo_heredado(response: Any, letra: str) -> None:
    """Exige un 422 cuyo detalle enumere "masculino" y "femenino".

    Args:
        response: Respuesta HTTP de la peticion con el sexo heredado.
        letra: La inicial enviada, solo para el mensaje de fallo.
    """
    assert response.status_code == 422, (
        f"El sexo heredado {letra!r} fue aceptado con {response.status_code}; "
        "una letra nunca debe pasar la frontera del API."
    )
    detalle = str(response.json()["detail"])
    assert "masculino" in detalle, f"El error para {letra!r} no nombra 'masculino': {detalle}"
    assert "femenino" in detalle, f"El error para {letra!r} no nombra 'femenino': {detalle}"
