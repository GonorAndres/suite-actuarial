"""
Seguro de incendio y danos a propiedad.

Producto basico para inmuebles residenciales, comerciales e industriales.
"""

from decimal import Decimal, ROUND_HALF_UP


# Tasas base por millar segun tipo de construccion
TASAS_CONSTRUCCION: dict[str, Decimal] = {
    "concreto": Decimal("0.80"),
    "acero": Decimal("0.90"),
    "ladrillo": Decimal("1.00"),
    "mixta": Decimal("1.20"),
    "madera": Decimal("2.50"),
    "lamina": Decimal("3.00"),
}

# Factores de zona de riesgo para incendio
ZONAS_INCENDIO: dict[str, Decimal] = {
    "urbana_baja": Decimal("0.85"),
    "urbana_media": Decimal("1.00"),
    "urbana_alta": Decimal("1.15"),
    "industrial": Decimal("1.40"),
    "rural": Decimal("1.10"),
    "forestal": Decimal("1.60"),
}

# Factores segun uso del inmueble
FACTOR_USO: dict[str, Decimal] = {
    "habitacional": Decimal("1.00"),
    "comercial": Decimal("1.20"),
    "oficinas": Decimal("1.10"),
    "industrial": Decimal("1.50"),
    "bodega": Decimal("1.35"),
    "restaurante": Decimal("1.45"),
}


class SeguroIncendio:
    """
    Seguro de incendio y danos a propiedad.

    Calcula la prima anual con base en:
    - Valor del inmueble
    - Tipo de construccion
    - Zona de riesgo
    - Uso del inmueble
    """

    def __init__(
        self,
        valor_inmueble: Decimal,
        tipo_construccion: str,
        zona: str,
        uso: str,
    ) -> None:
        """
        Args:
            valor_inmueble: valor de reposicion del inmueble en pesos MXN.
            tipo_construccion: tipo de construccion (ver TASAS_CONSTRUCCION).
            zona: zona de riesgo (ver ZONAS_INCENDIO).
            uso: uso del inmueble (ver FACTOR_USO).
        """
        if valor_inmueble <= 0:
            raise ValueError("El valor del inmueble debe ser positivo.")
        if tipo_construccion not in TASAS_CONSTRUCCION:
            raise ValueError(
                f"Tipo de construccion desconocido: {tipo_construccion}. "
                f"Opciones: {list(TASAS_CONSTRUCCION)}"
            )
        if zona not in ZONAS_INCENDIO:
            raise ValueError(
                f"Zona desconocida: {zona}. "
                f"Opciones: {list(ZONAS_INCENDIO)}"
            )
        if uso not in FACTOR_USO:
            raise ValueError(
                f"Uso desconocido: {uso}. "
                f"Opciones: {list(FACTOR_USO)}"
            )

        self.valor_inmueble = valor_inmueble
        self.tipo_construccion = tipo_construccion
        self.zona = zona
        self.uso = uso

        self.tasa_base = TASAS_CONSTRUCCION[tipo_construccion]
        self.factor_zona = ZONAS_INCENDIO[zona]
        self.factor_uso = FACTOR_USO[uso]

    def calcular_prima(self) -> Decimal:
        """
        Calcula la prima anual de incendio.

        Prima = (valor / 1000) * tasa_base * factor_zona * factor_uso

        Returns:
            Prima anual en pesos MXN.
        """
        prima = (
            (self.valor_inmueble / Decimal("1000"))
            * self.tasa_base
            * self.factor_zona
            * self.factor_uso
        )
        return prima.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def generar_cotizacion(self) -> dict:
        """Cotizacion completa con desglose de factores."""
        return {
            "valor_inmueble": self.valor_inmueble,
            "tipo_construccion": self.tipo_construccion,
            "tasa_base": self.tasa_base,
            "zona": self.zona,
            "factor_zona": self.factor_zona,
            "uso": self.uso,
            "factor_uso": self.factor_uso,
            "prima_anual": self.calcular_prima(),
        }
