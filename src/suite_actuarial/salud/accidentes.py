"""
Seguro de Accidentes y Enfermedades (A&E).

Cobertura mas simple que GMM, orientada a eventos de accidente:
- Muerte accidental
- Perdidas organicas (extremidades, vista, oido)
- Indemnizacion diaria por hospitalizacion
- Gastos funerarios

Referencia: CUSF Titulo 5, Capitulo de Accidentes y Enfermedades
"""

from decimal import ROUND_HALF_UP, Decimal


class AccidentesEnfermedades:
    """
    Seguro de Accidentes y Enfermedades (A&E).

    Calcula primas basadas en:
    - Banda de edad
    - Factor de ocupacion (riesgo laboral)
    - Suma asegurada

    Genera tabla de indemnizaciones con porcentajes estandar
    del mercado mexicano.
    """

    # Base rates by age group (per mille of sum insured, annual)
    TASAS_BASE = {
        "18-30": Decimal("2.5"),
        "31-40": Decimal("3.0"),
        "41-50": Decimal("4.5"),
        "51-60": Decimal("7.0"),
        "61-70": Decimal("12.0"),
    }

    # Occupation risk factors
    FACTORES_OCUPACION = {
        "oficina": Decimal("1.00"),
        "comercio": Decimal("1.10"),
        "industrial_ligero": Decimal("1.30"),
        "industrial_pesado": Decimal("1.60"),
        "alto_riesgo": Decimal("2.20"),
    }

    # Indemnification percentages (% of sum insured)
    TABLA_PERDIDAS_ORGANICAS = {
        "muerte_accidental": Decimal("1.00"),       # 100% SA
        "perdida_ambas_manos": Decimal("1.00"),
        "perdida_ambos_pies": Decimal("1.00"),
        "perdida_vista_ambos_ojos": Decimal("1.00"),
        "perdida_una_mano_un_pie": Decimal("1.00"),
        "perdida_una_mano": Decimal("0.60"),
        "perdida_un_pie": Decimal("0.60"),
        "perdida_vista_un_ojo": Decimal("0.50"),
        "perdida_pulgar": Decimal("0.25"),
        "perdida_indice": Decimal("0.15"),
        "perdida_oido_ambos": Decimal("0.50"),
        "perdida_oido_uno": Decimal("0.25"),
    }

    # Daily hospitalization benefit (fraction of sum insured, per day)
    TASA_INDEMNIZACION_DIARIA_DEFAULT = Decimal("0.001")  # 0.1% SA per day

    # Funeral expenses (fixed fraction of sum insured)
    FACTOR_GASTOS_FUNERARIOS = Decimal("0.10")  # 10% SA

    def __init__(
        self,
        edad: int,
        sexo: str,
        suma_asegurada: Decimal,
        ocupacion: str = "oficina",
        indemnizacion_diaria: Decimal | None = None,
    ) -> None:
        """
        Args:
            edad: Edad del asegurado (18-70).
            sexo: 'M' (masculino) o 'F' (femenino).
            suma_asegurada: Suma asegurada en MXN.
            ocupacion: Clase de riesgo ocupacional.
            indemnizacion_diaria: Monto diario por hospitalizacion.
                Si None, se calcula como 0.1% de la SA.
        """
        if not (18 <= edad <= 70):
            raise ValueError(
                "La edad debe estar entre 18 y 70 anos para A&E."
            )
        if sexo not in ("M", "F"):
            raise ValueError("El sexo debe ser 'M' o 'F'.")
        if suma_asegurada <= 0:
            raise ValueError("La suma asegurada debe ser positiva.")
        if ocupacion not in self.FACTORES_OCUPACION:
            raise ValueError(
                f"Ocupacion no valida: {ocupacion}. "
                f"Opciones: {list(self.FACTORES_OCUPACION)}"
            )

        self.edad = edad
        self.sexo = sexo
        self.suma_asegurada = Decimal(str(suma_asegurada))
        self.ocupacion = ocupacion
        self.indemnizacion_diaria = (
            Decimal(str(indemnizacion_diaria))
            if indemnizacion_diaria is not None
            else (self.suma_asegurada * self.TASA_INDEMNIZACION_DIARIA_DEFAULT).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )

    def _obtener_banda_edad(self) -> str:
        """Map age to the corresponding rate band."""
        if self.edad <= 30:
            return "18-30"
        elif self.edad <= 40:
            return "31-40"
        elif self.edad <= 50:
            return "41-50"
        elif self.edad <= 60:
            return "51-60"
        else:
            return "61-70"

    def calcular_prima(self) -> Decimal:
        """
        Calculate annual premium.

        Formula: (SA / 1000) * tasa_base * factor_ocupacion
        """
        banda = self._obtener_banda_edad()
        tasa = self.TASAS_BASE[banda]
        factor_ocup = self.FACTORES_OCUPACION[self.ocupacion]

        prima = (self.suma_asegurada / Decimal("1000")) * tasa * factor_ocup
        return prima.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def tabla_indemnizaciones(self) -> dict:
        """
        Table of benefits: death, organic losses, daily, funeral.

        Returns:
            Dict with all benefit amounts in MXN.
        """
        perdidas_organicas = {}
        for concepto, porcentaje in self.TABLA_PERDIDAS_ORGANICAS.items():
            monto = (self.suma_asegurada * porcentaje).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            perdidas_organicas[concepto] = {
                "porcentaje": porcentaje,
                "monto": monto,
            }

        gastos_funerarios = (
            self.suma_asegurada * self.FACTOR_GASTOS_FUNERARIOS
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "suma_asegurada": self.suma_asegurada,
            "perdidas_organicas": perdidas_organicas,
            "indemnizacion_diaria": {
                "monto_diario": self.indemnizacion_diaria,
                "monto_mensual": (self.indemnizacion_diaria * Decimal("30")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
            },
            "gastos_funerarios": gastos_funerarios,
            "prima_anual": self.calcular_prima(),
        }
