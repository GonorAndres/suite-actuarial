"""
Método Bootstrap para cálculo de reservas con distribución completa.

El Bootstrap proporciona la distribución completa de posibles valores
de reserva mediante simulación Monte Carlo, permitiendo calcular
percentiles y medidas de incertidumbre.
"""

from decimal import Decimal
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from mexican_insurance.core.validators import (
    ConfiguracionBootstrap,
    MetodoReserva,
    ResultadoReserva,
)
from mexican_insurance.reservas.chain_ladder import ChainLadder
from mexican_insurance.reservas.triangulo import (
    calcular_age_to_age,
    obtener_ultima_diagonal,
    validar_triangulo,
)


class Bootstrap:
    """
    Implementación del método Bootstrap para cálculo de reservas.

    El método Bootstrap:
    1. Ejecuta Chain Ladder en el triángulo original (modelo base)
    2. Calcula residuales: (observado - esperado) / sqrt(esperado)
    3. Genera N triángulos sintéticos re-muestreando residuales
    4. Ejecuta Chain Ladder en cada triángulo sintético
    5. Obtiene distribución de reservas posibles
    6. Calcula percentiles (P50, P75, P90, P95, P99)

    Ventajas:
    - Proporciona distribución completa, no solo punto estimado
    - Permite calcular capital económico (VaR, TVaR)
    - Cuantifica la incertidumbre del proceso
    - No asume distribución paramétrica

    Ejemplo:
        >>> config = ConfiguracionBootstrap(
        ...     num_simulaciones=1000,
        ...     seed=42,
        ...     percentiles=[50, 75, 90, 95, 99]
        ... )
        >>> bs = Bootstrap(config)
        >>> resultado = bs.calcular(triangulo)
        >>> print(f"Reserva P50: ${resultado.percentiles[50]:,.2f}")
        >>> print(f"Reserva P99: ${resultado.percentiles[99]:,.2f}")
    """

    def __init__(self, config: ConfiguracionBootstrap):
        """
        Inicializa el método Bootstrap.

        Args:
            config: Configuración del método
        """
        self.config = config
        self.chain_ladder: Optional[ChainLadder] = None
        self.triangulo_ajustado: Optional[pd.DataFrame] = None
        self.residuales: Optional[pd.DataFrame] = None
        self.simulaciones_reservas: Optional[List[Decimal]] = None

        # Fijar semilla para reproducibilidad
        if self.config.seed is not None:
            np.random.seed(self.config.seed)

    def calcular_triangulo_ajustado(
        self, triangulo: pd.DataFrame, cl: ChainLadder
    ) -> pd.DataFrame:
        """
        Calcula el triángulo ajustado (fitted values) del Chain Ladder.

        Args:
            triangulo: Triángulo original
            cl: Chain Ladder ya ejecutado

        Returns:
            Triángulo con valores ajustados
        """
        # Obtener factores de desarrollo
        factores = cl.factores_desarrollo

        # Crear triángulo ajustado
        triangulo_ajustado = pd.DataFrame(
            index=triangulo.index, columns=triangulo.columns, dtype=float
        )

        # La primera columna es igual a la original
        triangulo_ajustado.iloc[:, 0] = triangulo.iloc[:, 0]

        # Calcular valores ajustados usando factores
        for i in range(len(triangulo)):
            for j in range(1, triangulo.shape[1]):
                # Valor anterior
                valor_prev = triangulo_ajustado.iloc[i, j - 1]

                if pd.notna(valor_prev) and j < len(factores):
                    # Aplicar factor
                    valor_ajustado = float(valor_prev) * float(factores[j - 1])
                    triangulo_ajustado.iloc[i, j] = valor_ajustado
                else:
                    triangulo_ajustado.iloc[i, j] = None

        return triangulo_ajustado

    def calcular_residuales_pearson(
        self, triangulo: pd.DataFrame, triangulo_ajustado: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calcula residuales de Pearson.

        Fórmula:
            r[i,j] = (observado[i,j] - esperado[i,j]) / sqrt(esperado[i,j])

        Args:
            triangulo: Triángulo original (observado)
            triangulo_ajustado: Triángulo ajustado (esperado)

        Returns:
            DataFrame con residuales de Pearson
        """
        residuales = pd.DataFrame(
            index=triangulo.index, columns=triangulo.columns, dtype=float
        )

        for i in range(len(triangulo)):
            for j in range(triangulo.shape[1]):
                obs = triangulo.iloc[i, j]
                esp = triangulo_ajustado.iloc[i, j]

                if pd.notna(obs) and pd.notna(esp) and esp > 0:
                    # Residual de Pearson
                    r = (obs - esp) / np.sqrt(esp)
                    residuales.iloc[i, j] = r
                else:
                    residuales.iloc[i, j] = None

        return residuales

    def generar_triangulo_sintetico(
        self, triangulo_ajustado: pd.DataFrame, residuales: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Genera un triángulo sintético re-muestreando residuales.

        Args:
            triangulo_ajustado: Valores ajustados
            residuales: Residuales de Pearson

        Returns:
            Triángulo sintético
        """
        # Extraer residuales válidos (no-NaN)
        residuales_validos = residuales.values.flatten()
        residuales_validos = residuales_validos[~np.isnan(residuales_validos)]

        if len(residuales_validos) == 0:
            # Fallback: retornar triángulo ajustado
            return triangulo_ajustado.copy()

        # Crear triángulo sintético
        triangulo_sintetico = triangulo_ajustado.copy()

        # Verificar si los residuales tienen variación significativa
        # Nota: Cuando el ajuste Chain Ladder es perfecto o casi perfecto,
        # todos los residuales son ≈0 y el bootstrap no tiene variación.
        # En este caso, agregamos ruido sintético basado en proceso de Poisson.
        std_residuales = np.std(residuales_validos)

        if std_residuales < 0.01:  # Threshold: residuales con std < 1%
            # Residuales son esencialmente cero - agregar ruido sintético Poisson
            # Esto asegura variación incluso cuando el ajuste es perfecto
            for i in range(len(triangulo_ajustado)):
                for j in range(triangulo_ajustado.shape[1]):
                    esp = triangulo_ajustado.iloc[i, j]

                    if pd.notna(esp) and esp > 0:
                        # Ruido Poisson: var = mean
                        # Generar valor de distribución Poisson centrada en esp
                        valor_poisson = np.random.poisson(max(1, esp))
                        # Asegurar no-negativo
                        triangulo_sintetico.iloc[i, j] = max(0, float(valor_poisson))
        else:
            # Re-muestrear residuales para cada celda (método estándar)
            for i in range(len(triangulo_ajustado)):
                for j in range(triangulo_ajustado.shape[1]):
                    esp = triangulo_ajustado.iloc[i, j]

                    if pd.notna(esp) and esp > 0:
                        # Re-muestrear un residual
                        r_sample = np.random.choice(residuales_validos)

                        # Generar valor sintético
                        # valor_sintetico = esperado + residual * sqrt(esperado)
                        valor_sintetico = esp + r_sample * np.sqrt(esp)

                        # Asegurar no-negativo
                        valor_sintetico = max(0, valor_sintetico)

                        triangulo_sintetico.iloc[i, j] = valor_sintetico

        return triangulo_sintetico

    def ejecutar_simulacion(
        self, triangulo: pd.DataFrame, cl_base: ChainLadder
    ) -> Decimal:
        """
        Ejecuta una simulación Bootstrap completa.

        Args:
            triangulo: Triángulo original
            cl_base: Chain Ladder base (para estructura)

        Returns:
            Reserva total de esta simulación
        """
        # 1. Generar triángulo sintético
        triangulo_sintetico = self.generar_triangulo_sintetico(
            self.triangulo_ajustado, self.residuales
        )

        # 2. Ejecutar Chain Ladder en triángulo sintético
        from mexican_insurance.core.validators import ConfiguracionChainLadder

        config_cl = ConfiguracionChainLadder()
        cl_sim = ChainLadder(config_cl)

        try:
            resultado_sim = cl_sim.calcular(triangulo_sintetico)
            return resultado_sim.reserva_total
        except Exception:
            # Si falla la simulación, retornar reserva base
            return cl_base.calcular(triangulo).reserva_total

    def calcular_percentiles(
        self, simulaciones: List[Decimal]
    ) -> Dict[int, Decimal]:
        """
        Calcula percentiles de las simulaciones.

        Args:
            simulaciones: Lista de reservas simuladas

        Returns:
            Diccionario {percentil: valor}
        """
        # Convertir a numpy array
        valores = np.array([float(s) for s in simulaciones])

        percentiles = {}
        for p in self.config.percentiles:
            valor = np.percentile(valores, p)
            percentiles[p] = Decimal(str(valor))

        return percentiles

    def calcular(self, triangulo: pd.DataFrame) -> ResultadoReserva:
        """
        Ejecuta el método Bootstrap completo.

        Args:
            triangulo: Triángulo de desarrollo (acumulado)

        Returns:
            ResultadoReserva con distribución completa
        """
        # Validar triángulo
        validar_triangulo(triangulo)

        # Resetear semilla para asegurar reproducibilidad
        # Nota: Esto es necesario porque la semilla se establece en __init__,
        # pero si se crean múltiples instancias de Bootstrap, la segunda
        # sobrescribe el estado del generador aleatorio global de numpy.
        if self.config.seed is not None:
            np.random.seed(self.config.seed)

        # 1. Ejecutar Chain Ladder base
        from mexican_insurance.core.validators import ConfiguracionChainLadder

        config_cl = ConfiguracionChainLadder()
        self.chain_ladder = ChainLadder(config_cl)
        resultado_base = self.chain_ladder.calcular(triangulo)

        # 2. Calcular triángulo ajustado
        self.triangulo_ajustado = self.calcular_triangulo_ajustado(
            triangulo, self.chain_ladder
        )

        # 3. Calcular residuales
        if self.config.metodo_residuales == "pearson":
            self.residuales = self.calcular_residuales_pearson(
                triangulo, self.triangulo_ajustado
            )
        else:
            # Fallback a Pearson
            self.residuales = self.calcular_residuales_pearson(
                triangulo, self.triangulo_ajustado
            )

        # 4. Ejecutar simulaciones
        self.simulaciones_reservas = []

        for sim in range(self.config.num_simulaciones):
            reserva_sim = self.ejecutar_simulacion(
                triangulo, self.chain_ladder
            )
            self.simulaciones_reservas.append(reserva_sim)

        # 5. Calcular percentiles
        percentiles = self.calcular_percentiles(self.simulaciones_reservas)

        # 6. Estadísticas descriptivas
        valores_sim = np.array(
            [float(s) for s in self.simulaciones_reservas]
        )
        media = Decimal(str(np.mean(valores_sim)))
        desv_std = Decimal(str(np.std(valores_sim)))
        minimo = Decimal(str(np.min(valores_sim)))
        maximo = Decimal(str(np.max(valores_sim)))

        # 7. Usar mediana (P50) como estimador central
        reserva_total = percentiles[50]

        # Pagado total = última diagonal
        ultima_diagonal = obtener_ultima_diagonal(triangulo)
        pagado_total = sum(Decimal(str(v)) for v in ultima_diagonal)

        # Ultimate total = pagado + reserva
        ultimate_total = pagado_total + reserva_total

        # 8. Construir detalles
        detalles = {
            "num_simulaciones": self.config.num_simulaciones,
            "seed": self.config.seed,
            "metodo_residuales": self.config.metodo_residuales,
            "media": str(media),
            "desviacion_estandar": str(desv_std),
            "minimo": str(minimo),
            "maximo": str(maximo),
            "coeficiente_variacion": (
                str(desv_std / media) if media > 0 else "0"
            ),
            "reserva_base_cl": str(resultado_base.reserva_total),
        }

        # 9. Construir resultado
        # Nota: Para Bootstrap no calculamos reservas_por_anio detalladas
        # ya que cada simulación tiene valores diferentes
        resultado = ResultadoReserva(
            metodo=MetodoReserva.BOOTSTRAP,
            reserva_total=reserva_total,
            ultimate_total=ultimate_total,
            pagado_total=pagado_total,
            reservas_por_anio=resultado_base.reservas_por_anio,  # Usar base
            ultimates_por_anio=resultado_base.ultimates_por_anio,  # Usar base
            factores_desarrollo=self.chain_ladder.factores_desarrollo,
            percentiles=percentiles,
            detalles=detalles,
        )

        return resultado

    def obtener_distribucion(self) -> Optional[List[Decimal]]:
        """
        Obtiene la distribución completa de reservas simuladas.

        Returns:
            Lista de reservas simuladas o None si no se ha calculado
        """
        return self.simulaciones_reservas

    def graficar_distribucion(self) -> pd.DataFrame:
        """
        Genera datos para graficar la distribución de reservas.

        Returns:
            DataFrame con bins y frecuencias
        """
        if self.simulaciones_reservas is None:
            raise ValueError(
                "Debe ejecutar calcular() antes de graficar distribución"
            )

        valores = np.array([float(s) for s in self.simulaciones_reservas])

        # Crear histograma
        counts, bin_edges = np.histogram(valores, bins=50)

        # Crear DataFrame
        df_hist = pd.DataFrame(
            {
                "bin_start": bin_edges[:-1],
                "bin_end": bin_edges[1:],
                "frequency": counts,
                "relative_frequency": counts / len(valores),
            }
        )

        return df_hist

    def calcular_var(self, nivel_confianza: float = 0.95) -> Decimal:
        """
        Calcula Value at Risk (VaR) al nivel de confianza dado.

        VaR = percentil correspondiente a (1 - nivel_confianza)

        Args:
            nivel_confianza: Nivel de confianza (ej: 0.95 = 95%)

        Returns:
            VaR en unidades monetarias
        """
        if self.simulaciones_reservas is None:
            raise ValueError("Debe ejecutar calcular() antes de calcular VaR")

        percentil = int(nivel_confianza * 100)
        valores = np.array([float(s) for s in self.simulaciones_reservas])
        var = np.percentile(valores, percentil)

        return Decimal(str(var))

    def calcular_tvar(self, nivel_confianza: float = 0.95) -> Decimal:
        """
        Calcula Tail Value at Risk (TVaR) o Expected Shortfall.

        TVaR = promedio de valores que exceden el VaR

        Args:
            nivel_confianza: Nivel de confianza (ej: 0.95 = 95%)

        Returns:
            TVaR en unidades monetarias
        """
        if self.simulaciones_reservas is None:
            raise ValueError("Debe ejecutar calcular() antes de calcular TVaR")

        var = float(self.calcular_var(nivel_confianza))
        valores = np.array([float(s) for s in self.simulaciones_reservas])

        # Valores que exceden VaR
        tail_values = valores[valores >= var]

        if len(tail_values) == 0:
            return Decimal(str(var))

        tvar = np.mean(tail_values)
        return Decimal(str(tvar))

    def __repr__(self) -> str:
        """Representación string del método"""
        return (
            f"Bootstrap("
            f"sims={self.config.num_simulaciones}, "
            f"seed={self.config.seed})"
        )
