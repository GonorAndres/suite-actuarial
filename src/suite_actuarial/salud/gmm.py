"""
Producto de Gastos Medicos Mayores (GMM).

El GMM es el producto de seguro de salud mas comun en Mexico.
Cubre gastos medicos mayores por encima de un deducible, con coaseguro
y tope de coaseguro, dentro de una red hospitalaria definida por
nivel y zona geografica.

Estructura tipica mexicana:
- Suma asegurada: 1M - 100M MXN
- Deducible: 10,000 - 500,000 MXN
- Coaseguro: 10-30% pagado por el asegurado
- Tope de coaseguro: limite maximo que paga el asegurado por coaseguro
- Nivel hospitalario: determina red de hospitales

La prima se calcula por bandas de edad quinquenales (0-4, 5-9, ..., 60-64, 65+).

Referencia: Circular Unica de Seguros y Fianzas (CUSF), CNSF
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import StrEnum


class NivelHospitalario(StrEnum):
    ESTANDAR = "estandar"
    MEDIO = "medio"
    ALTO = "alto"


class ZonaGeografica(StrEnum):
    METRO = "metro"       # CDMX, Monterrey, Guadalajara
    URBANO = "urbano"     # Other large cities
    FORANEO = "foraneo"   # Small cities and rural


class GMM:
    """
    Gastos Medicos Mayores (Major Medical Insurance).

    Calcula primas ajustadas por:
    - Banda de edad quinquenal
    - Zona geografica
    - Nivel hospitalario
    - Deducible
    - Coaseguro

    Tambien simula la distribucion de un gasto medico entre asegurado
    y aseguradora (deducible, coaseguro, tope).
    """

    # Age-band base rates (annual per-mille of sum insured)
    # These are per-band base rates before zone/level adjustments
    TASAS_BANDA_EDAD = {
        "0-4": Decimal("8.5"),
        "5-9": Decimal("4.2"),
        "10-14": Decimal("3.8"),
        "15-19": Decimal("4.5"),
        "20-24": Decimal("5.0"),
        "25-29": Decimal("5.8"),
        "30-34": Decimal("7.2"),
        "35-39": Decimal("9.0"),
        "40-44": Decimal("12.5"),
        "45-49": Decimal("17.0"),
        "50-54": Decimal("24.0"),
        "55-59": Decimal("33.0"),
        "60-64": Decimal("45.0"),
        "65+": Decimal("62.0"),
    }

    FACTORES_ZONA = {
        ZonaGeografica.METRO: Decimal("1.20"),
        ZonaGeografica.URBANO: Decimal("1.00"),
        ZonaGeografica.FORANEO: Decimal("0.85"),
    }

    FACTORES_NIVEL = {
        NivelHospitalario.ESTANDAR: Decimal("0.80"),
        NivelHospitalario.MEDIO: Decimal("1.00"),
        NivelHospitalario.ALTO: Decimal("1.30"),
    }

    # Deductible discount factors (higher deductible = lower premium)
    FACTORES_DEDUCIBLE = {
        Decimal("10000"): Decimal("1.40"),
        Decimal("25000"): Decimal("1.15"),
        Decimal("50000"): Decimal("1.00"),   # Base
        Decimal("100000"): Decimal("0.80"),
        Decimal("250000"): Decimal("0.60"),
        Decimal("500000"): Decimal("0.45"),
    }

    # Coinsurance factors (higher coinsurance = lower premium)
    FACTORES_COASEGURO = {
        Decimal("0.10"): Decimal("1.00"),  # 10% coinsurance (standard)
        Decimal("0.20"): Decimal("0.90"),
        Decimal("0.30"): Decimal("0.82"),
    }

    def __init__(
        self,
        edad: int,
        sexo: str,
        suma_asegurada: Decimal,
        deducible: Decimal,
        coaseguro_pct: Decimal,
        tope_coaseguro: Decimal | None = None,
        zona: ZonaGeografica = ZonaGeografica.URBANO,
        nivel: NivelHospitalario = NivelHospitalario.MEDIO,
        margen_operativo: Decimal = Decimal("0.30"),
    ) -> None:
        """
        Args:
            edad: Edad del asegurado (0-110).
            sexo: 'M' (masculino) o 'F' (femenino).
            suma_asegurada: Suma asegurada en MXN (>= 1,000,000).
            deducible: Monto del deducible en MXN.
            coaseguro_pct: Porcentaje de coaseguro (ej: 0.10 = 10%).
            tope_coaseguro: Tope maximo de coaseguro en MXN (None = sin tope).
            zona: Zona geografica del asegurado.
            nivel: Nivel hospitalario de la poliza.
        """
        if not (0 <= edad <= 110):
            raise ValueError("La edad debe estar entre 0 y 110 anos.")
        if sexo not in ("M", "F"):
            raise ValueError("El sexo debe ser 'M' o 'F'.")
        if suma_asegurada < Decimal("1000000"):
            raise ValueError(
                "La suma asegurada minima para GMM es 1,000,000 MXN."
            )
        if deducible < 0:
            raise ValueError("El deducible no puede ser negativo.")
        if not (Decimal("0") < coaseguro_pct <= Decimal("1")):
            raise ValueError(
                "El porcentaje de coaseguro debe estar entre 0 (exclusivo) y 1."
            )
        if tope_coaseguro is not None and tope_coaseguro < 0:
            raise ValueError("El tope de coaseguro no puede ser negativo.")
        if not isinstance(zona, ZonaGeografica):
            raise ValueError(
                f"Zona no valida: {zona}. "
                f"Opciones: {[z.value for z in ZonaGeografica]}"
            )
        if not isinstance(nivel, NivelHospitalario):
            raise ValueError(
                f"Nivel no valido: {nivel}. "
                f"Opciones: {[n.value for n in NivelHospitalario]}"
            )

        self.edad = edad
        self.sexo = sexo
        self.suma_asegurada = Decimal(str(suma_asegurada))
        self.deducible = Decimal(str(deducible))
        self.coaseguro_pct = Decimal(str(coaseguro_pct))
        self.tope_coaseguro = (
            Decimal(str(tope_coaseguro)) if tope_coaseguro is not None else None
        )
        self.zona = zona
        self.nivel = nivel
        self.margen_operativo = Decimal(str(margen_operativo))

    def _obtener_banda_edad(self) -> str:
        """Map age to quinquennial band."""
        if self.edad >= 65:
            return "65+"
        # Quinquennial bands: 0-4, 5-9, ..., 60-64
        inicio = (self.edad // 5) * 5
        fin = inicio + 4
        return f"{inicio}-{fin}"

    def _obtener_factor_deducible(self) -> Decimal:
        """
        Get deductible factor, interpolating linearly if the deductible
        is not in the standard table.
        """
        # If exact match exists, use it
        if self.deducible in self.FACTORES_DEDUCIBLE:
            return self.FACTORES_DEDUCIBLE[self.deducible]

        # Sort deductible levels for interpolation
        niveles = sorted(self.FACTORES_DEDUCIBLE.keys())

        # Clamp to boundaries
        if self.deducible <= niveles[0]:
            return self.FACTORES_DEDUCIBLE[niveles[0]]
        if self.deducible >= niveles[-1]:
            return self.FACTORES_DEDUCIBLE[niveles[-1]]

        # Find surrounding levels and interpolate linearly
        for i in range(len(niveles) - 1):
            if niveles[i] <= self.deducible <= niveles[i + 1]:
                d_low = niveles[i]
                d_high = niveles[i + 1]
                f_low = self.FACTORES_DEDUCIBLE[d_low]
                f_high = self.FACTORES_DEDUCIBLE[d_high]
                # Linear interpolation
                proporcion = (self.deducible - d_low) / (d_high - d_low)
                factor = f_low + proporcion * (f_high - f_low)
                return factor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # Fallback (should not reach here)
        return Decimal("1.00")

    def _obtener_factor_coaseguro(self) -> Decimal:
        """Get coinsurance factor; use exact match or closest lower."""
        if self.coaseguro_pct in self.FACTORES_COASEGURO:
            return self.FACTORES_COASEGURO[self.coaseguro_pct]

        # Find closest key that does not exceed the given coinsurance
        niveles = sorted(self.FACTORES_COASEGURO.keys())
        factor = self.FACTORES_COASEGURO[niveles[0]]  # default
        for n in niveles:
            if n <= self.coaseguro_pct:
                factor = self.FACTORES_COASEGURO[n]
        return factor

    def calcular_prima_base(self) -> Decimal:
        """
        Base premium from age band and sum insured.

        Formula: (suma_asegurada / 1000) * tasa_banda_edad
        """
        banda = self._obtener_banda_edad()
        tasa = self.TASAS_BANDA_EDAD[banda]
        prima = (self.suma_asegurada / Decimal("1000")) * tasa
        return prima.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calcular_prima_ajustada(self) -> Decimal:
        """
        Premium after all factor adjustments.

        Ajustes aplicados:
        1. Factor de zona geografica
        2. Factor de nivel hospitalario
        3. Factor de deducible
        4. Factor de coaseguro
        """
        prima = self.calcular_prima_base()
        factor_zona = self.FACTORES_ZONA[self.zona]
        factor_nivel = self.FACTORES_NIVEL[self.nivel]
        factor_deducible = self._obtener_factor_deducible()
        factor_coaseguro = self._obtener_factor_coaseguro()

        prima_ajustada = prima * factor_zona * factor_nivel * factor_deducible * factor_coaseguro
        return prima_ajustada.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def siniestralidad_esperada(self) -> Decimal:
        """
        Expected claims for this risk profile.

        Aproximacion: prima_ajustada / (1 + margen_operativo)
        Se asume un margen operativo del 30% (gastos de administracion,
        adquisicion y utilidad).
        """
        prima = self.calcular_prima_ajustada()
        siniestralidad = prima / (Decimal("1") + self.margen_operativo)
        return siniestralidad.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def desglose_prima(self) -> dict:
        """
        Detailed breakdown: base, each factor, adjustments, final.

        Returns:
            Dict with complete premium decomposition.
        """
        banda = self._obtener_banda_edad()
        tasa = self.TASAS_BANDA_EDAD[banda]
        prima_base = self.calcular_prima_base()
        factor_zona = self.FACTORES_ZONA[self.zona]
        factor_nivel = self.FACTORES_NIVEL[self.nivel]
        factor_deducible = self._obtener_factor_deducible()
        factor_coaseguro = self._obtener_factor_coaseguro()
        prima_ajustada = self.calcular_prima_ajustada()
        siniestralidad = self.siniestralidad_esperada()

        return {
            "asegurado": {
                "edad": self.edad,
                "sexo": self.sexo,
                "banda_edad": banda,
            },
            "producto": {
                "suma_asegurada": self.suma_asegurada,
                "deducible": self.deducible,
                "coaseguro_pct": self.coaseguro_pct,
                "tope_coaseguro": self.tope_coaseguro,
                "zona": self.zona.value,
                "nivel": self.nivel.value,
            },
            "tarificacion": {
                "tasa_banda_edad": tasa,
                "prima_base": prima_base,
                "factor_zona": factor_zona,
                "factor_nivel": factor_nivel,
                "factor_deducible": factor_deducible,
                "factor_coaseguro": factor_coaseguro,
                "prima_ajustada": prima_ajustada,
            },
            "siniestralidad_esperada": siniestralidad,
        }

    def simular_gasto_medico(self, monto_reclamacion: Decimal) -> dict:
        """
        Given a claim amount, show how deductible/coinsurance/tope apply.

        Logica:
        1. Si el monto <= deducible: asegurado paga todo
        2. Monto excedente = monto - deducible
        3. Coaseguro del asegurado = excedente * coaseguro_pct
        4. Si hay tope de coaseguro, se limita el coaseguro del asegurado
        5. Aseguradora paga = excedente - coaseguro_asegurado
        6. Si el monto excede la suma asegurada, el exceso no se cubre

        Args:
            monto_reclamacion: Monto total de la reclamacion medica.

        Returns:
            Dict con desglose del gasto entre asegurado y aseguradora.
        """
        monto = Decimal(str(monto_reclamacion))
        if monto < 0:
            raise ValueError("El monto de reclamacion no puede ser negativo.")

        # Monto cubierto limitado a la suma asegurada
        monto_cubierto = min(monto, self.suma_asegurada)
        exceso_no_cubierto = max(Decimal("0"), monto - self.suma_asegurada)

        # Deducible
        if monto_cubierto <= self.deducible:
            return {
                "monto_reclamacion": monto,
                "deducible_aplicado": monto_cubierto,
                "monto_excedente": Decimal("0"),
                "coaseguro_asegurado": Decimal("0"),
                "pago_aseguradora": Decimal("0"),
                "pago_total_asegurado": monto_cubierto + exceso_no_cubierto,
                "exceso_no_cubierto": exceso_no_cubierto,
            }

        monto_excedente = monto_cubierto - self.deducible

        # Coaseguro del asegurado
        coaseguro_asegurado = (monto_excedente * self.coaseguro_pct).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Aplicar tope de coaseguro
        if self.tope_coaseguro is not None:
            coaseguro_asegurado = min(coaseguro_asegurado, self.tope_coaseguro)

        # Pago de la aseguradora
        pago_aseguradora = (monto_excedente - coaseguro_asegurado).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Total que paga el asegurado
        pago_asegurado = (
            self.deducible + coaseguro_asegurado + exceso_no_cubierto
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "monto_reclamacion": monto,
            "deducible_aplicado": self.deducible,
            "monto_excedente": monto_excedente,
            "coaseguro_asegurado": coaseguro_asegurado,
            "pago_aseguradora": pago_aseguradora,
            "pago_total_asegurado": pago_asegurado,
            "exceso_no_cubierto": exceso_no_cubierto,
        }
