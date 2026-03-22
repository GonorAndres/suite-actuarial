"""
Motor de tarificacion y credibilidad actuarial para seguros de danos.

Incluye:
- Credibilidad de Buhlmann y Buhlmann-Straub
- Sistema de Bonus-Malus para autos
- Tabla de factores de tarificacion
"""

from decimal import ROUND_HALF_UP, Decimal


class FactorCredibilidad:
    """
    Credibilidad actuarial (Buhlmann y Buhlmann-Straub).

    Permite combinar la experiencia propia de una poliza/grupo
    con la experiencia del portafolio completo.
    """

    @staticmethod
    def buhlmann(experiencia_propia: list[Decimal], prima_manual: Decimal) -> dict:
        """
        Credibilidad de Buhlmann clasica.

        Z = n / (n + k), donde k = varianza_proceso / varianza_hipotetica
        Prima credibilidad = Z * experiencia_media + (1 - Z) * prima_manual

        Args:
            experiencia_propia: lista de perdidas observadas por periodo.
            prima_manual: prima del portafolio (manual rate).

        Returns:
            dict con Z, k, prima_credibilidad, experiencia_media.
        """
        n = len(experiencia_propia)
        if n == 0:
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "experiencia_media": Decimal("0"),
                "n_periodos": 0,
            }

        # Media de experiencia propia
        media = sum(experiencia_propia) / n

        if n < 2:
            # Con un solo periodo no se puede estimar varianza;
            # Z = 0, se usa prima manual completa.
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "experiencia_media": media.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "n_periodos": n,
            }

        # Varianza de proceso (within): promedio de la varianza de cada observacion
        # Aproximamos la varianza del proceso como la media (modelo Poisson-like)
        varianza_proceso = media

        # Varianza hipotetica (between): varianza de las medias observadas
        varianza_hipotetica = sum((x - media) ** 2 for x in experiencia_propia) / (n - 1)

        # Ajuste: restar componente de proceso de la varianza entre periodos
        varianza_hipotetica_neta = varianza_hipotetica - varianza_proceso / Decimal(str(n))

        if varianza_hipotetica_neta <= 0:
            # No hay variacion entre periodos; toda la variacion es proceso
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "experiencia_media": media.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "n_periodos": n,
            }

        k = (varianza_proceso / varianza_hipotetica_neta).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        z = (Decimal(str(n)) / (Decimal(str(n)) + k)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        prima_cred = (z * media + (1 - z) * prima_manual).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "Z": z,
            "k": k,
            "prima_credibilidad": prima_cred,
            "experiencia_media": media.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "n_periodos": n,
        }

    @staticmethod
    def buhlmann_straub(
        experiencias: list[dict], prima_manual: Decimal
    ) -> dict:
        """
        Buhlmann-Straub (ponderado por exposicion).

        Cada elemento de experiencias es:
            {"siniestros": Decimal, "exposicion": int}

        La credibilidad se pondera por la exposicion de cada periodo,
        dando mas peso a periodos con mayor volumen.

        Args:
            experiencias: lista de dicts con siniestros y exposicion.
            prima_manual: prima del portafolio.

        Returns:
            dict con Z, k, prima_credibilidad, tasa_propia.
        """
        if not experiencias:
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "tasa_propia": Decimal("0"),
                "exposicion_total": 0,
            }

        n = len(experiencias)
        exposicion_total = sum(e["exposicion"] for e in experiencias)

        if exposicion_total == 0:
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "tasa_propia": Decimal("0"),
                "exposicion_total": 0,
            }

        # Tasa propia ponderada por exposicion
        tasa_propia = sum(
            e["siniestros"] for e in experiencias
        ) / Decimal(str(exposicion_total))

        if n < 2:
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "tasa_propia": tasa_propia.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                "exposicion_total": exposicion_total,
            }

        # Varianza de proceso (within)
        varianza_proceso = Decimal("0")
        for e in experiencias:
            m_i = e["exposicion"]
            if m_i > 0:
                tasa_i = e["siniestros"] / Decimal(str(m_i))
                varianza_proceso += Decimal(str(m_i)) * (tasa_i - tasa_propia) ** 2

        varianza_proceso = varianza_proceso / Decimal(str(n - 1))

        # Varianza hipotetica
        m_total = Decimal(str(exposicion_total))
        m_sq_sum = sum(Decimal(str(e["exposicion"])) ** 2 for e in experiencias)
        c = m_total - m_sq_sum / m_total

        if c <= 0:
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "tasa_propia": tasa_propia.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                "exposicion_total": exposicion_total,
            }

        varianza_hipotetica = (varianza_proceso - tasa_propia) / c
        if varianza_hipotetica <= 0:
            varianza_hipotetica = varianza_proceso / c

        if varianza_hipotetica <= 0:
            return {
                "Z": Decimal("0"),
                "k": None,
                "prima_credibilidad": prima_manual,
                "tasa_propia": tasa_propia.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                "exposicion_total": exposicion_total,
            }

        k = (varianza_proceso / varianza_hipotetica / m_total).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        # Z ponderada por exposicion total
        z_denom = Decimal("1") + k
        z = (Decimal("1") / z_denom).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        z = max(Decimal("0"), min(z, Decimal("1")))

        prima_cred = (z * tasa_propia + (1 - z) * prima_manual).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "Z": z,
            "k": k,
            "prima_credibilidad": prima_cred,
            "tasa_propia": tasa_propia.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "exposicion_total": exposicion_total,
        }


class CalculadoraBonusMalus:
    """
    Sistema de Bonus-Malus para seguros de auto en Mexico.

    Escala tipica mexicana:
    - Sin siniestros: descuento acumulativo (-5% por ano, max -30%)
    - Con siniestro: recargo (+15% a +50% dependiendo del numero)
    """

    # Escala estandar mexicana
    NIVELES: dict[int, Decimal] = {
        -5: Decimal("0.70"),   # Max descuento: 30%
        -4: Decimal("0.75"),
        -3: Decimal("0.80"),
        -2: Decimal("0.85"),
        -1: Decimal("0.90"),
         0: Decimal("1.00"),   # Base
         1: Decimal("1.15"),
         2: Decimal("1.30"),
         3: Decimal("1.50"),   # Max recargo: 50%
    }

    NIVEL_MIN = -5
    NIVEL_MAX = 3

    def __init__(self, nivel_actual: int = 0) -> None:
        """
        Args:
            nivel_actual: nivel BMS actual (default 0 = base).
        """
        if nivel_actual < self.NIVEL_MIN or nivel_actual > self.NIVEL_MAX:
            raise ValueError(
                f"Nivel debe estar entre {self.NIVEL_MIN} y {self.NIVEL_MAX}, "
                f"recibido: {nivel_actual}"
            )
        self.nivel_actual = nivel_actual

    def transicion(self, siniestros_periodo: int) -> int:
        """
        Calcula el nuevo nivel BMS despues de un periodo.

        Reglas:
        - 0 siniestros: baja 1 nivel (mas descuento)
        - 1 siniestro: sube 2 niveles
        - 2+ siniestros: sube 3 niveles

        Returns:
            Nuevo nivel BMS.
        """
        if siniestros_periodo < 0:
            raise ValueError("Los siniestros no pueden ser negativos.")

        if siniestros_periodo == 0:
            nuevo = self.nivel_actual - 1
        elif siniestros_periodo == 1:
            nuevo = self.nivel_actual + 2
        else:
            nuevo = self.nivel_actual + 3

        # Clamp a los limites
        nuevo = max(self.NIVEL_MIN, min(self.NIVEL_MAX, nuevo))
        self.nivel_actual = nuevo
        return nuevo

    def factor_actual(self) -> Decimal:
        """Factor de prima del nivel actual."""
        return self.NIVELES[self.nivel_actual]

    def historial_completo(self, historial_siniestros: list[int]) -> list[dict]:
        """
        Dado un historial de siniestros anuales, traza la ruta BMS completa.

        Args:
            historial_siniestros: lista de conteos de siniestros por ano.

        Returns:
            Lista de dicts con ano, siniestros, nivel, factor.
        """
        resultado = []
        for i, siniestros in enumerate(historial_siniestros):
            nivel_previo = self.nivel_actual
            self.transicion(siniestros)
            resultado.append({
                "ano": i + 1,
                "siniestros": siniestros,
                "nivel_previo": nivel_previo,
                "nivel_nuevo": self.nivel_actual,
                "factor": self.factor_actual(),
            })
        return resultado


class TablaTarifas:
    """
    Tabla de factores de tarificacion con busqueda y aplicacion.

    Permite cargar una estructura de factores y aplicarlos
    a una prima base.
    """

    def __init__(self, factores: dict) -> None:
        """
        Args:
            factores: dict anidado de factores de tarificacion.
                Ejemplo: {"zona": {"cdmx": Decimal("1.30")}, "edad": {"18-25": Decimal("1.35")}}
        """
        self.factores = factores

    def obtener_factor(self, **kwargs: str) -> Decimal:
        """
        Busca un factor en la tabla.

        Args:
            **kwargs: pares dimension=valor. Solo acepta un par a la vez.
                Ejemplo: zona="cdmx"

        Returns:
            El factor correspondiente.
        """
        if len(kwargs) != 1:
            raise ValueError("Debe proporcionar exactamente una dimension.")

        dimension, valor = next(iter(kwargs.items()))

        if dimension not in self.factores:
            raise KeyError(f"Dimension no encontrada: {dimension}. "
                           f"Disponibles: {list(self.factores)}")

        tabla = self.factores[dimension]
        if valor not in tabla:
            raise KeyError(f"Valor '{valor}' no encontrado en dimension '{dimension}'. "
                           f"Disponibles: {list(tabla)}")

        return tabla[valor]

    def aplicar_factores(self, prima_base: Decimal, **kwargs: str) -> Decimal:
        """
        Aplica multiples factores de tarificacion a una prima base.

        Args:
            prima_base: prima base antes de factores.
            **kwargs: pares dimension=valor.
                Ejemplo: aplicar_factores(prima_base, zona="cdmx", edad="18-25")

        Returns:
            Prima ajustada despues de aplicar todos los factores.
        """
        resultado = prima_base
        for dimension, valor in kwargs.items():
            factor = self.obtener_factor(**{dimension: valor})
            resultado = (resultado * factor).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        return resultado
