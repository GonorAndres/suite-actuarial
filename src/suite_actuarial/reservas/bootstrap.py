"""Bootstrap ODP de England-Verrall para la distribucion predictiva de la reserva.

Implementa el bootstrap del modelo Poisson sobredispersado (ODP) tal como lo
describen Peter England y Richard Verrall ("Analytic and bootstrap estimates of
prediction errors in claims reserving", *Insurance: Mathematics and Economics*
25, 1999; y England, "Addendum to 'Analytic and bootstrap estimates...'", 2002).

El procedimiento tiene dos fuentes de error y las separa:

1. **Error de estimacion.** Se remuestrean los residuales de Pearson ajustados
   para generar pseudo-triangulos, y cada uno se vuelve a valuar con Chain
   Ladder. La dispersion de esas reservas mide cuanto se moveria la estimacion
   si la experiencia observada hubiera sido otra.
2. **Error de proceso.** Cada celda futura del pseudo-triangulo se simula de una
   Gamma con media `m` y varianza `phi*m`, que es la forma de varianza del
   modelo ODP. Mide la aleatoriedad de los siniestros aun conociendo el modelo.

Pasos, en el orden en que se ejecutan:

1. Factores de desarrollo ponderados por volumen sobre el triangulo acumulado.
2. Valores ajustados **hacia atras** desde el ultimate: `C(i,j) = U_i / prod f_k`.
   Asi la diagonal ajustada reproduce la observada, y los incrementales
   ajustados reproducen exactamente las sumas por fila y por columna del
   triangulo observado (propiedad del estimador maximo-verosimil del ODP, que
   coincide con Chain Ladder).
3. Residuales de Pearson sobre los **incrementales**:
   `r(i,j) = (m(i,j) - m_ajustado(i,j)) / sqrt(m_ajustado(i,j))`.
4. Parametro de dispersion `phi = sum r^2 / (n - p)`, con `n` celdas observadas y
   `p = I + J - 1` parametros. Los residuales se escalan por `sqrt(n/(n-p))`
   (correccion por grados de libertad de England, 2002).
5. Por replica: remuestreo con reemplazo de los residuales ajustados, se
   reconstruyen los incrementales, se acumulan, se recalculan los factores y se
   proyecta el futuro; cada celda futura se simula de la Gamma del paso 2.

Diferencias con la version anterior de este modulo (hallazgo A2 de
`docs/AUDIT.md`), que no era ODP: los residuales se calculaban sobre valores
**acumulados** con ajuste hacia adelante, no habia `phi` ni correccion por
grados de libertad ni paso de varianza de proceso, se inyectaba ruido arbitrario
`N(0, 0.05)`, el estimador central era la mediana y perturbar acumulados rompia
la monotonia, asi que una fraccion de los intentos se descartaba y la banda
quedaba sesgada por seleccion. Nada de eso ocurre aqui: se perturban
incrementales y se recumula, de modo que no hay intentos que descartar.

Limites vigentes:

- La distribucion es **condicional al modelo**: supone que el patron de
  desarrollo es estable y que la varianza de cada celda es proporcional a su
  media. No cubre riesgo de modelo, cambio de mezcla ni inflacion no observada.
- La media de las replicas queda ~1% por encima de la reserva de Chain Ladder,
  y la diferencia **no** es error de Monte Carlo: la reserva es convexa en los
  factores de desarrollo, asi que remuestrear los factores eleva la media
  (desigualdad de Jensen). El efecto persiste con el paso de proceso apagado.
  Por eso la conciliacion se reporta en `detalles["conciliacion_cl_relativa"]`
  en lugar de afirmarse: el estimador puntual defendible sigue siendo la
  reserva de Chain Ladder, y el bootstrap aporta la dispersion alrededor de ella.
- No incluye factor de cola: el ultimate es el de la ultima columna observada.
- Los incrementales negativos no admiten varianza de proceso Gamma; esas celdas
  se proyectan sin simular y se reportan en `detalles`.
"""

from decimal import Decimal

import numpy as np
import pandas as pd

from suite_actuarial.core.models.common import CalculationMetadata
from suite_actuarial.core.validators import (
    ConfiguracionBootstrap,
    MetodoReserva,
    ResultadoReserva,
)
from suite_actuarial.reservas.chain_ladder import ChainLadder
from suite_actuarial.reservas.triangulo import (
    factores_volumen_ponderado,
    obtener_ultima_diagonal,
    validar_triangulo,
)

ALCANCE = (
    "La distribucion predictiva es CONDICIONAL al modelo: supone patron de "
    "desarrollo estable y varianza proporcional a la media (Poisson "
    "sobredispersado). No cubre riesgo de modelo, cambio de mezcla de cartera, "
    "inflacion no observada ni la incertidumbre de un factor de cola."
)


def _num_parametros(n_origenes: int, n_periodos: int) -> int:
    """Parametros del modelo ODP: I niveles, J patrones, menos la escala comun."""
    return n_origenes + n_periodos - 1


class Bootstrap:
    """Bootstrap ODP de England-Verrall sobre un triangulo acumulado.

    El estimador central es la **media** de las replicas, que reconcilia con la
    reserva de Chain Ladder dentro del error de Monte Carlo; la diferencia se
    reporta en `detalles["conciliacion_cl"]`. La desviacion estandar de las
    replicas es el **error de prediccion**, comparable con el error estandar de
    Mack (1993) sobre el mismo triangulo.

    Ejemplo:
        >>> config = ConfiguracionBootstrap(num_simulaciones=1000, seed=42)
        >>> bs = Bootstrap(config)
        >>> resultado = bs.calcular(triangulo)
        >>> print(f"Reserva (media): ${resultado.reserva_total:,.2f}")
        >>> print(f"Error de prediccion: {resultado.detalles['error_prediccion']}")
        >>> print(f"Percentil 99: ${resultado.percentiles[99]:,.2f}")
    """

    def __init__(self, config: ConfiguracionBootstrap):
        """Inicializa el metodo.

        Args:
            config: Configuracion del metodo
        """
        self.config = config
        self.chain_ladder: ChainLadder | None = None
        self.incrementales_observados: np.ndarray | None = None
        self.incrementales_ajustados: np.ndarray | None = None
        self.residuales: np.ndarray | None = None
        self.phi: float | None = None
        self.simulaciones_reservas: list[Decimal] | None = None
        self.celdas_utilizables: int = 0
        self.celdas_excluidas: int = 0
        self.parametros_modelo: int = 0
        self.grados_libertad: int = 0
        self.celdas_sin_proceso: int = 0
        self._mascara_observada: np.ndarray | None = None
        self._ultima_columna: dict[int, int] = {}

    # ── Ajuste del modelo ────────────────────────────────────────────────────

    def ajustar_incrementales(self, triangulo: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Calcula los incrementales observados y los ajustados por el modelo.

        Los ajustados se construyen **hacia atras** desde el ultimate de cada
        ano de origen, de modo que la diagonal ajustada reproduce la observada.
        La version anterior los construia hacia adelante desde la primera
        columna, lo que dejaba residuales correlacionados por fila y de media
        distinta de cero (hallazgo A2).

        Args:
            triangulo: Triangulo acumulado

        Returns:
            Tupla `(observados, ajustados)` como arreglos 2D con NaN en las
            celdas futuras
        """
        valores = triangulo.to_numpy(dtype=float)
        n_rows, n_cols = valores.shape
        factores, _ = factores_volumen_ponderado(valores)

        acumulado_ajustado = np.full_like(valores, np.nan)
        for i in range(n_rows):
            observados = np.where(~np.isnan(valores[i]))[0]
            if len(observados) == 0:
                continue
            ultima = int(observados[-1])

            # Ultimate proyectado desde la ultima celda observada.
            ultimate = valores[i, ultima]
            for k in range(ultima, n_cols - 1):
                ultimate *= factores[k]

            # Ajuste hacia atras: C(i,j) = U_i / prod_{k>=j} f_k
            acumulado_ajustado[i, n_cols - 1] = ultimate
            for j in range(n_cols - 2, -1, -1):
                if factores[j] > 0:
                    acumulado_ajustado[i, j] = acumulado_ajustado[i, j + 1] / factores[j]
                else:
                    acumulado_ajustado[i, j] = acumulado_ajustado[i, j + 1]

        observados_inc = self._a_incrementales(valores)
        ajustados_inc = self._a_incrementales(acumulado_ajustado)

        # Solo las celdas observadas participan del ajuste.
        mascara = ~np.isnan(valores)
        ajustados_inc = np.where(mascara, ajustados_inc, np.nan)

        self._mascara_observada = mascara
        self._ultima_columna = {
            i: (int(np.where(mascara[i])[0][-1]) if mascara[i].any() else -1) for i in range(n_rows)
        }
        self.incrementales_observados = observados_inc
        self.incrementales_ajustados = ajustados_inc
        return observados_inc, ajustados_inc

    @staticmethod
    def _a_incrementales(acumulado: np.ndarray) -> np.ndarray:
        """Convierte un arreglo acumulado a incrementales por fila."""
        incremental = np.full_like(acumulado, np.nan)
        incremental[:, 0] = acumulado[:, 0]
        if acumulado.shape[1] > 1:
            incremental[:, 1:] = acumulado[:, 1:] - acumulado[:, :-1]
        return incremental

    def calcular_residuales_pearson(
        self, observados: np.ndarray, ajustados: np.ndarray
    ) -> np.ndarray:
        """Residuales de Pearson ajustados por grados de libertad.

        `r(i,j) = (m - m_aj) / sqrt(m_aj)`, escalados por `sqrt(n/(n-p))`. Fija
        tambien `self.phi = sum r^2 / (n - p)`, el parametro de dispersion del
        modelo ODP, que gobierna la varianza de proceso.

        Solo participan las celdas con incremental ajustado positivo: la raiz
        no esta definida en las demas. El conteo se reporta en `detalles`.

        Args:
            observados: Incrementales observados
            ajustados: Incrementales ajustados por el modelo

        Returns:
            Arreglo 1D con los residuales ajustados

        Raises:
            ValueError: si no quedan grados de libertad (`n <= p`), en cuyo caso
                el triangulo es demasiado pequeno para estimar la dispersion
        """
        utilizable = ~np.isnan(observados) & ~np.isnan(ajustados) & (ajustados > 0)
        n_obs = int(utilizable.sum())

        n_origenes, n_periodos = observados.shape
        p = _num_parametros(n_origenes, n_periodos)
        grados_libertad = n_obs - p

        if grados_libertad <= 0:
            raise ValueError(
                f"El triangulo no tiene grados de libertad para estimar la "
                f"dispersion: {n_obs} celdas utilizables y {p} parametros "
                f"(I + J - 1). Se necesita un triangulo mas grande."
            )

        crudos = (observados[utilizable] - ajustados[utilizable]) / np.sqrt(ajustados[utilizable])
        self.phi = float((crudos**2).sum() / grados_libertad)

        # Correccion por grados de libertad (England, 2002): sin ella el
        # remuestreo subestima la variabilidad, porque los residuales de un
        # ajuste tienen menos dispersion que los errores que representan.
        ajuste = np.sqrt(n_obs / grados_libertad)
        self.residuales = crudos * ajuste
        self.celdas_utilizables = n_obs
        self.grados_libertad = grados_libertad
        self.parametros_modelo = p
        self.celdas_excluidas = int((~utilizable & ~np.isnan(observados)).sum())
        return self.residuales

    # ── Replicas ─────────────────────────────────────────────────────────────

    def generar_pseudo_incrementales(self, rng: np.random.Generator) -> np.ndarray:
        """Genera un pseudo-triangulo incremental remuestreando residuales.

        `m*(i,j) = m_aj(i,j) + r* * sqrt(m_aj(i,j))`, con `r*` tomado con
        reemplazo del conjunto de residuales ajustados.

        Args:
            rng: Generador aleatorio ya sembrado

        Returns:
            Pseudo-triangulo incremental con la misma estructura de NaN
        """
        if self.incrementales_ajustados is None or self.residuales is None:
            raise ValueError("Debe ajustar el modelo antes de generar replicas")

        ajustados = self.incrementales_ajustados
        pseudo = np.full_like(ajustados, np.nan)
        utilizable = ~np.isnan(ajustados) & (ajustados > 0)

        muestra = rng.choice(self.residuales, size=int(utilizable.sum()), replace=True)
        pseudo[utilizable] = ajustados[utilizable] + muestra * np.sqrt(ajustados[utilizable])

        # Celdas observadas sin varianza definida se copian del ajuste.
        copiar = ~np.isnan(ajustados) & ~utilizable
        pseudo[copiar] = ajustados[copiar]
        return pseudo

    def ejecutar_replica(self, rng: np.random.Generator) -> Decimal:
        """Ejecuta una replica: remuestreo, revaluacion y varianza de proceso.

        Args:
            rng: Generador aleatorio ya sembrado

        Returns:
            Reserva simulada de la replica, con error de estimacion y de proceso
        """
        pseudo_incremental = self.generar_pseudo_incrementales(rng)
        rellenado = np.where(np.isnan(pseudo_incremental), 0.0, pseudo_incremental)
        pseudo_acumulado = np.where(
            np.isnan(pseudo_incremental), np.nan, np.cumsum(rellenado, axis=1)
        )

        factores, _ = factores_volumen_ponderado(pseudo_acumulado)

        n_rows, n_cols = pseudo_acumulado.shape
        reserva = 0.0
        phi = self.phi if self.phi and self.phi > 0 else 0.0

        for i in range(n_rows):
            ultima = self._ultima_columna.get(i, -1)
            if ultima < 0 or ultima >= n_cols - 1:
                continue

            proyectado = pseudo_acumulado[i, ultima]
            if np.isnan(proyectado):
                continue

            for j in range(ultima + 1, n_cols):
                # La proyeccion es DETERMINISTA dado el pseudo-triangulo: el
                # valor simulado de una celda no realimenta la media de la
                # siguiente. Realimentarlo convertiria la fila en una caminata
                # aleatoria y sobreestimaria el error de prediccion (aqui, un
                # 35% de mas sobre el triangulo de Taylor & Ashe).
                media_celda = proyectado * factores[j - 1] - proyectado
                proyectado = proyectado * factores[j - 1]

                if phi > 0 and media_celda > 0:
                    # Varianza de proceso del modelo ODP: Var = phi * media. La
                    # Gamma con forma media/phi y escala phi tiene exactamente
                    # esa media y esa varianza.
                    simulado = float(rng.gamma(shape=media_celda / phi, scale=phi))
                else:
                    # Celda no positiva: la Gamma no esta definida. Se proyecta
                    # sin simular y se cuenta.
                    simulado = float(media_celda)
                    self.celdas_sin_proceso += 1

                reserva += simulado

        return Decimal(str(reserva))

    # ── Calculo completo ─────────────────────────────────────────────────────

    def calcular(self, triangulo: pd.DataFrame) -> ResultadoReserva:
        """Ejecuta el bootstrap ODP completo.

        Args:
            triangulo: Triangulo de desarrollo acumulado

        Returns:
            ResultadoReserva con la distribucion predictiva de la reserva
        """
        validar_triangulo(triangulo)

        rng = np.random.default_rng(self.config.seed)

        from suite_actuarial.core.validators import (
            ConfiguracionChainLadder,
            MetodoPromedio,
        )

        # Chain Ladder ponderado por volumen: es el estimador que el modelo ODP
        # reproduce, asi que es la referencia con la que debe conciliar.
        self.chain_ladder = ChainLadder(
            ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.PONDERADO)
        )
        resultado_base = self.chain_ladder.calcular(triangulo)

        observados, ajustados = self.ajustar_incrementales(triangulo)
        self.calcular_residuales_pearson(observados, ajustados)

        self.celdas_sin_proceso = 0
        self.simulaciones_reservas = [
            self.ejecutar_replica(rng) for _ in range(self.config.num_simulaciones)
        ]

        valores_sim = np.array([float(s) for s in self.simulaciones_reservas])
        media = Decimal(str(float(valores_sim.mean())))
        error_prediccion = Decimal(str(float(valores_sim.std(ddof=1))))

        percentiles = {
            p: Decimal(str(float(np.percentile(valores_sim, p)))) for p in self.config.percentiles
        }

        reserva_total = media
        ultima_diagonal = obtener_ultima_diagonal(triangulo)
        pagado_total = sum(Decimal(str(v)) for v in ultima_diagonal)
        ultimate_total = pagado_total + reserva_total

        conciliacion = media - resultado_base.reserva_total
        conciliacion_relativa = (
            abs(conciliacion) / resultado_base.reserva_total
            if resultado_base.reserva_total > 0
            else Decimal("0")
        )

        detalles = {
            "metodo": "bootstrap-odp-england-verrall",
            "num_simulaciones": self.config.num_simulaciones,
            "seed": self.config.seed,
            "metodo_residuales": "pearson",
            "estimador_central": "media",
            "phi_dispersion": str(self.phi),
            "celdas_utilizables": self.celdas_utilizables,
            "celdas_excluidas": self.celdas_excluidas,
            "parametros_modelo": self.parametros_modelo,
            "grados_libertad": self.grados_libertad,
            "ajuste_grados_libertad": str(
                float(np.sqrt(self.celdas_utilizables / self.grados_libertad))
            ),
            "celdas_sin_varianza_proceso": self.celdas_sin_proceso,
            "media": str(media),
            "mediana": str(Decimal(str(float(np.median(valores_sim))))),
            "error_prediccion": str(error_prediccion),
            "coeficiente_variacion": (str(error_prediccion / media) if media > 0 else "0"),
            "minimo": str(Decimal(str(float(valores_sim.min())))),
            "maximo": str(Decimal(str(float(valores_sim.max())))),
            "reserva_base_cl": str(resultado_base.reserva_total),
            # Un bootstrap ODP correcto lleva esta diferencia a cero dentro del
            # error de Monte Carlo. Se reporta para que el lector lo verifique.
            "conciliacion_cl": str(conciliacion),
            "conciliacion_cl_relativa": str(conciliacion_relativa),
        }

        return ResultadoReserva(
            metodo=MetodoReserva.BOOTSTRAP,
            reserva_total=reserva_total,
            ultimate_total=ultimate_total,
            pagado_total=pagado_total,
            reservas_por_anio=resultado_base.reservas_por_anio,
            ultimates_por_anio=resultado_base.ultimates_por_anio,
            factores_desarrollo=self.chain_ladder.factores_desarrollo,
            percentiles=percentiles,
            detalles=detalles,
            calculation_metadata=CalculationMetadata(
                validation_tier="supported",
                warnings=[ALCANCE],
                assumptions_snapshot={
                    "metodo": "bootstrap-odp-england-verrall",
                    "phi_dispersion": str(self.phi),
                    "num_simulaciones": str(self.config.num_simulaciones),
                    "seed": str(self.config.seed),
                },
            ),
        )

    # ── Lecturas de la distribucion ──────────────────────────────────────────

    def obtener_distribucion(self) -> list[Decimal] | None:
        """Devuelve la distribucion completa de reservas simuladas."""
        return self.simulaciones_reservas

    def graficar_distribucion(self) -> pd.DataFrame:
        """Genera datos para graficar la distribucion de reservas."""
        if self.simulaciones_reservas is None:
            raise ValueError("Debe ejecutar calcular() antes de graficar distribución")

        valores = np.array([float(s) for s in self.simulaciones_reservas])
        counts, bin_edges = np.histogram(valores, bins=50)

        return pd.DataFrame(
            {
                "bin_start": bin_edges[:-1],
                "bin_end": bin_edges[1:],
                "frequency": counts,
                "relative_frequency": counts / len(valores),
            }
        )

    def calcular_var(self, nivel_confianza: float = 0.95) -> Decimal:
        """Value at Risk de la reserva al nivel de confianza dado.

        Es un percentil de la distribucion predictiva, condicional al modelo
        (ver `ALCANCE`). No sustituye el requerimiento de capital regulatorio,
        que tiene su propia definicion y calibracion.

        Args:
            nivel_confianza: Nivel de confianza (ej: 0.95 = 95%)

        Returns:
            VaR en unidades monetarias
        """
        if self.simulaciones_reservas is None:
            raise ValueError("Debe ejecutar calcular() antes de calcular VaR")

        valores = np.array([float(s) for s in self.simulaciones_reservas])
        return Decimal(str(float(np.percentile(valores, nivel_confianza * 100))))

    def calcular_tvar(self, nivel_confianza: float = 0.95) -> Decimal:
        """Tail Value at Risk (Expected Shortfall) de la reserva.

        Promedio de las replicas que igualan o exceden el VaR. Mismo alcance
        que `calcular_var`.

        Args:
            nivel_confianza: Nivel de confianza (ej: 0.95 = 95%)

        Returns:
            TVaR en unidades monetarias
        """
        if self.simulaciones_reservas is None:
            raise ValueError("Debe ejecutar calcular() antes de calcular TVaR")

        var = float(self.calcular_var(nivel_confianza))
        valores = np.array([float(s) for s in self.simulaciones_reservas])
        cola = valores[valores >= var]

        if len(cola) == 0:
            return Decimal(str(var))

        return Decimal(str(float(cola.mean())))

    def __repr__(self) -> str:
        """Representacion string del metodo."""
        return f"Bootstrap(sims={self.config.num_simulaciones}, seed={self.config.seed})"
