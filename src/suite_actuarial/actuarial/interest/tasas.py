"""
Curva de rendimiento (yield curve) para valuaciones actuariales.

Soporta:
- Tasas spot
- Tasas forward
- Factores de descuento
- Interpolacion lineal
- Valor presente de flujos de efectivo

Referencia: Banco de Mexico, vectores de precios de MBonos y CETES.
"""

from decimal import Decimal, ROUND_HALF_UP


class CurvaRendimiento:
    """
    Curva de rendimiento (yield curve) para valuaciones actuariales.

    Almacena tasas spot para plazos discretos y permite:
    - Interpolacion lineal para plazos intermedios
    - Calculo de tasas forward implicitas
    - Factores de descuento
    - Valor presente de flujos de efectivo

    Las tasas se expresan en forma decimal (ej: 0.08 = 8%).
    """

    def __init__(self, plazos: list[int], tasas: list[Decimal]) -> None:
        """
        Args:
            plazos: List of tenors in years [1, 2, 3, 5, 10, 20, 30].
            tasas: Corresponding annual spot rates [0.08, 0.085, ...].

        Raises:
            ValueError: If plazos and tasas have different lengths,
                are empty, or contain invalid values.
        """
        if len(plazos) != len(tasas):
            raise ValueError(
                "plazos y tasas deben tener la misma longitud."
            )
        if len(plazos) == 0:
            raise ValueError("Se requiere al menos un plazo y tasa.")
        if any(p <= 0 for p in plazos):
            raise ValueError("Todos los plazos deben ser positivos.")
        if any(t < 0 for t in tasas):
            raise ValueError("Las tasas no pueden ser negativas.")

        # Sort by tenor
        pares = sorted(zip(plazos, tasas))
        self.plazos = [p for p, _ in pares]
        self.tasas = [Decimal(str(t)) for _, t in pares]

    def tasa_spot(self, plazo: float) -> Decimal:
        """
        Spot rate for a given tenor (interpolated linearly if needed).

        Args:
            plazo: Tenor in years (can be fractional).

        Returns:
            Interpolated spot rate.

        Raises:
            ValueError: If plazo is non-positive.
        """
        if plazo <= 0:
            raise ValueError("El plazo debe ser positivo.")

        plazo_d = Decimal(str(plazo))

        # Exact match
        for i, p in enumerate(self.plazos):
            if Decimal(str(p)) == plazo_d:
                return self.tasas[i]

        # Below minimum: use first rate (flat extrapolation)
        if plazo_d < Decimal(str(self.plazos[0])):
            return self.tasas[0]

        # Above maximum: use last rate (flat extrapolation)
        if plazo_d > Decimal(str(self.plazos[-1])):
            return self.tasas[-1]

        # Linear interpolation between surrounding tenors
        for i in range(len(self.plazos) - 1):
            p_low = Decimal(str(self.plazos[i]))
            p_high = Decimal(str(self.plazos[i + 1]))
            if p_low <= plazo_d <= p_high:
                t_low = self.tasas[i]
                t_high = self.tasas[i + 1]
                proporcion = (plazo_d - p_low) / (p_high - p_low)
                tasa = t_low + proporcion * (t_high - t_low)
                return tasa.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

        # Fallback (should not reach here)
        return self.tasas[-1]

    def tasa_forward(self, t1: float, t2: float) -> Decimal:
        """
        Forward rate between t1 and t2.

        The forward rate f(t1, t2) satisfies:
            (1 + r(t2))^t2 = (1 + r(t1))^t1 * (1 + f(t1,t2))^(t2-t1)

        Args:
            t1: Start tenor in years.
            t2: End tenor in years (must be > t1).

        Returns:
            Implied forward rate between t1 and t2.

        Raises:
            ValueError: If t2 <= t1 or tenors are non-positive.
        """
        if t1 <= 0 or t2 <= 0:
            raise ValueError("Los plazos deben ser positivos.")
        if t2 <= t1:
            raise ValueError("t2 debe ser mayor que t1.")

        t1_d = Decimal(str(t1))
        t2_d = Decimal(str(t2))
        r1 = self.tasa_spot(t1)
        r2 = self.tasa_spot(t2)

        # (1 + r2)^t2 / (1 + r1)^t1 = (1 + f)^(t2 - t1)
        factor_t2 = (Decimal("1") + r2) ** t2_d
        factor_t1 = (Decimal("1") + r1) ** t1_d
        dt = t2_d - t1_d

        ratio = factor_t2 / factor_t1

        # f = ratio^(1/dt) - 1
        # Use float for the power operation, then convert back
        ratio_float = float(ratio)
        dt_float = float(dt)
        forward_float = ratio_float ** (1.0 / dt_float) - 1.0
        forward = Decimal(str(forward_float)).quantize(
            Decimal("0.000001"), rounding=ROUND_HALF_UP
        )

        return forward

    def factor_descuento(self, plazo: float) -> Decimal:
        """
        Discount factor v(t) = 1 / (1 + r(t))^t

        Args:
            plazo: Tenor in years.

        Returns:
            Discount factor for the given tenor.
        """
        if plazo <= 0:
            raise ValueError("El plazo debe ser positivo.")

        plazo_d = Decimal(str(plazo))
        r = self.tasa_spot(plazo)

        # v(t) = 1 / (1 + r)^t
        factor = Decimal("1") / ((Decimal("1") + r) ** plazo_d)
        return factor.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    def valor_presente(
        self, flujos: list[Decimal], plazos: list[float]
    ) -> Decimal:
        """
        Present value of a series of cashflows.

        PV = sum(flujo_i * v(t_i)) for each cashflow.

        Args:
            flujos: List of cashflow amounts.
            plazos: Corresponding payment times in years.

        Returns:
            Total present value.

        Raises:
            ValueError: If flujos and plazos have different lengths.
        """
        if len(flujos) != len(plazos):
            raise ValueError(
                "flujos y plazos deben tener la misma longitud."
            )

        pv = Decimal("0")
        for flujo, plazo in zip(flujos, plazos):
            flujo_d = Decimal(str(flujo))
            descuento = self.factor_descuento(plazo)
            pv += flujo_d * descuento

        return pv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def plana(cls, tasa: Decimal, plazo_max: int = 50) -> "CurvaRendimiento":
        """
        Create a flat yield curve (all tenors have the same rate).

        Args:
            tasa: Constant annual rate.
            plazo_max: Maximum tenor in years (default 50).

        Returns:
            CurvaRendimiento with a flat curve.
        """
        tasa_d = Decimal(str(tasa))
        plazos = list(range(1, plazo_max + 1))
        tasas = [tasa_d] * len(plazos)
        return cls(plazos, tasas)

    @classmethod
    def cetes_referencia(cls) -> "CurvaRendimiento":
        """
        Create a representative CETES/MBonos yield curve for Mexico.

        Based on approximate market levels (2024 reference):
        - CETES 28 dias ~11.00%
        - CETES 91 dias ~11.05%
        - CETES 182 dias ~10.95%
        - CETES 364 dias ~10.80%
        - MBonos 3 anos ~10.20%
        - MBonos 5 anos ~10.00%
        - MBonos 10 anos ~9.70%
        - MBonos 20 anos ~9.50%
        - MBonos 30 anos ~9.40%

        Returns:
            CurvaRendimiento with representative Mexican rates.
        """
        plazos = [1, 2, 3, 5, 10, 20, 30]
        tasas = [
            Decimal("0.1080"),  # 1 year
            Decimal("0.1050"),  # 2 years
            Decimal("0.1020"),  # 3 years
            Decimal("0.1000"),  # 5 years
            Decimal("0.0970"),  # 10 years
            Decimal("0.0950"),  # 20 years
            Decimal("0.0940"),  # 30 years
        ]
        return cls(plazos, tasas)
