"""
Seguro de responsabilidad civil general.

Producto para empresas y profesionales que cubre danos a terceros
causados por la actividad del asegurado.
"""

from decimal import ROUND_HALF_UP, Decimal

# Tasas base por millar segun clase de actividad
TASAS_ACTIVIDAD: dict[str, Decimal] = {
    "oficinas": Decimal("1.20"),
    "comercio_minorista": Decimal("1.80"),
    "restaurante": Decimal("2.50"),
    "manufactura_ligera": Decimal("3.00"),
    "manufactura_pesada": Decimal("4.50"),
    "construccion": Decimal("5.00"),
    "transporte": Decimal("4.00"),
    "servicios_profesionales": Decimal("1.50"),
    "salud": Decimal("3.50"),
    "educacion": Decimal("1.40"),
    "hoteleria": Decimal("2.20"),
    "inmobiliaria": Decimal("1.60"),
}

# Factores de deducible
FACTOR_DEDUCIBLE_RC: dict[Decimal, Decimal] = {
    Decimal("10000"): Decimal("1.10"),
    Decimal("25000"): Decimal("1.00"),
    Decimal("50000"): Decimal("0.90"),
    Decimal("100000"): Decimal("0.80"),
    Decimal("250000"): Decimal("0.70"),
}


class SeguroRC:
    """
    Seguro de responsabilidad civil general.

    Calcula la prima anual con base en:
    - Limite de responsabilidad
    - Deducible
    - Clase de actividad del asegurado
    """

    def __init__(
        self,
        limite_responsabilidad: Decimal,
        deducible: Decimal,
        clase_actividad: str,
    ) -> None:
        """
        Args:
            limite_responsabilidad: limite maximo de cobertura en pesos MXN.
            deducible: monto del deducible en pesos MXN.
            clase_actividad: tipo de actividad (ver TASAS_ACTIVIDAD).
        """
        if limite_responsabilidad <= 0:
            raise ValueError("El limite de responsabilidad debe ser positivo.")
        if deducible < 0:
            raise ValueError("El deducible no puede ser negativo.")
        if clase_actividad not in TASAS_ACTIVIDAD:
            raise ValueError(
                f"Clase de actividad desconocida: {clase_actividad}. "
                f"Opciones: {list(TASAS_ACTIVIDAD)}"
            )

        self.limite_responsabilidad = limite_responsabilidad
        self.deducible = deducible
        self.clase_actividad = clase_actividad

        self.tasa_base = TASAS_ACTIVIDAD[clase_actividad]

        # Buscar factor de deducible mas cercano
        self.factor_deducible = self._buscar_factor_deducible(deducible)

    @staticmethod
    def _buscar_factor_deducible(deducible: Decimal) -> Decimal:
        """Busca el factor de deducible mas cercano por debajo."""
        claves = sorted(FACTOR_DEDUCIBLE_RC.keys())
        factor = Decimal("1.10")  # Default si es menor al minimo
        for clave in claves:
            if deducible >= clave:
                factor = FACTOR_DEDUCIBLE_RC[clave]
        return factor

    def calcular_prima(self) -> Decimal:
        """
        Calcula la prima anual de RC.

        Prima = (limite / 1000) * tasa_base * factor_deducible

        Returns:
            Prima anual en pesos MXN.
        """
        prima = (
            (self.limite_responsabilidad / Decimal("1000"))
            * self.tasa_base
            * self.factor_deducible
        )
        return prima.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def generar_cotizacion(self) -> dict:
        """Cotizacion completa con desglose de factores."""
        return {
            "limite_responsabilidad": self.limite_responsabilidad,
            "deducible": self.deducible,
            "clase_actividad": self.clase_actividad,
            "tasa_base": self.tasa_base,
            "factor_deducible": self.factor_deducible,
            "prima_anual": self.calcular_prima(),
        }
