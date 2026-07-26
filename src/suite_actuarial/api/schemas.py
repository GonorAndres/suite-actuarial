"""Base compartida para los cuerpos de peticion del API.

Los routers traducen la peticion a objetos de dominio con
`Decimal(str(campo))`. `Decimal("inf")` se construye sin error, pero
`quantize()` sobre un valor no finito levanta `decimal.InvalidOperation`, que
ningun router captura: una peticion con `Infinity` terminaba en un 500 en vez
de un rechazo con motivo. Las clases de dominio son objetos de Python planos,
no modelos Pydantic, asi que no rechazan el valor por su cuenta.

`allow_inf_nan=False` corta eso en el borde, donde todavia se puede explicar
al llamador que su entrada no es un numero utilizable.
"""

from pydantic import BaseModel, ConfigDict


class SolicitudBase(BaseModel):
    """Cuerpo de peticion que rechaza flotantes no finitos (`inf`, `nan`)."""

    model_config = ConfigDict(allow_inf_nan=False)
