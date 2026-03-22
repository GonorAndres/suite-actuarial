"""
Modelo colectivo de riesgo (collective risk model) para seguros de danos.

S = X1 + X2 + ... + XN
donde N ~ distribucion de frecuencia, Xi ~ distribucion de severidad

Este modulo es el nucleo matematico de la tarificacion de seguros de
propiedad y casualidad (P&C / danos).
"""

from decimal import Decimal
from typing import Any

import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Mapeos de distribuciones
# ---------------------------------------------------------------------------

_DIST_FRECUENCIA = {
    "poisson": lambda p: stats.poisson(mu=p["lambda_"]),
    "negbinom": lambda p: stats.nbinom(n=p["n"], p=p["p"]),
    "binomial": lambda p: stats.binom(n=p["n"], p=p["p"]),
}

_DIST_SEVERIDAD = {
    "lognormal": lambda p: stats.lognorm(s=p["sigma"], scale=np.exp(p["mu"])),
    "pareto": lambda p: stats.pareto(b=p["alpha"], scale=p["scale"]),
    "gamma": lambda p: stats.gamma(a=p["alpha"], scale=1.0 / p["beta"]),
    "weibull": lambda p: stats.weibull_min(c=p["c"], scale=p["scale"]),
    "exponencial": lambda p: stats.expon(scale=1.0 / p["lambda_"]),
}


class ModeloColectivo:
    """
    Modelo colectivo de riesgo (collective risk model).

    S = X1 + X2 + ... + XN
    donde N ~ distribucion de frecuencia, Xi ~ distribucion de severidad

    Soporta:
        Frecuencia: poisson, negbinom, binomial
        Severidad: lognormal, pareto, gamma, weibull, exponencial
    """

    def __init__(
        self,
        dist_frecuencia: str,
        params_frecuencia: dict[str, Any],
        dist_severidad: str,
        params_severidad: dict[str, Any],
    ) -> None:
        """
        Args:
            dist_frecuencia: "poisson" | "negbinom" | "binomial"
            params_frecuencia: parametros de la distribucion de frecuencia
                poisson:  {"lambda_": float}
                negbinom: {"n": float, "p": float}
                binomial: {"n": int, "p": float}
            dist_severidad: "lognormal" | "pareto" | "gamma" | "weibull" | "exponencial"
            params_severidad: parametros de la distribucion de severidad
                lognormal:    {"mu": float, "sigma": float}
                pareto:       {"alpha": float, "scale": float}
                gamma:        {"alpha": float, "beta": float}
                weibull:      {"c": float, "scale": float}
                exponencial:  {"lambda_": float}
        """
        if dist_frecuencia not in _DIST_FRECUENCIA:
            raise ValueError(
                f"Distribucion de frecuencia no soportada: {dist_frecuencia}. "
                f"Opciones: {list(_DIST_FRECUENCIA)}"
            )
        if dist_severidad not in _DIST_SEVERIDAD:
            raise ValueError(
                f"Distribucion de severidad no soportada: {dist_severidad}. "
                f"Opciones: {list(_DIST_SEVERIDAD)}"
            )

        self.dist_frecuencia_nombre = dist_frecuencia
        self.dist_severidad_nombre = dist_severidad
        self.params_frecuencia = params_frecuencia
        self.params_severidad = params_severidad

        self._freq = _DIST_FRECUENCIA[dist_frecuencia](params_frecuencia)
        self._sev = _DIST_SEVERIDAD[dist_severidad](params_severidad)

        # Cache de simulacion
        self._cache_sim: np.ndarray | None = None
        self._cache_seed: int | None = None
        self._cache_n: int | None = None

    # ------------------------------------------------------------------
    # Momentos analiticos
    # ------------------------------------------------------------------

    def prima_pura(self) -> Decimal:
        """E[S] = E[N] * E[X] -- perdida agregada esperada."""
        en = float(self._freq.mean())
        ex = float(self._sev.mean())
        return Decimal(str(round(en * ex, 2)))

    def varianza_agregada(self) -> Decimal:
        """Var[S] = E[N]*Var[X] + Var[N]*E[X]^2"""
        en = float(self._freq.mean())
        vn = float(self._freq.var())
        ex = float(self._sev.mean())
        vx = float(self._sev.var())
        var_s = en * vx + vn * ex**2
        return Decimal(str(round(var_s, 2)))

    def desviacion_estandar(self) -> Decimal:
        """Desviacion estandar de la perdida agregada."""
        var_s = float(self.varianza_agregada())
        return Decimal(str(round(var_s**0.5, 2)))

    # ------------------------------------------------------------------
    # Simulacion Monte Carlo
    # ------------------------------------------------------------------

    def simular_perdidas(
        self, n_simulaciones: int = 10_000, seed: int | None = None
    ) -> np.ndarray:
        """
        Simulacion Monte Carlo de perdidas agregadas.

        Para cada simulacion:
            1. Muestrear N ~ frecuencia
            2. Muestrear X1, ..., XN ~ severidad
            3. S = sum(Xi)

        Returns:
            Array de longitud n_simulaciones con perdidas agregadas.
        """
        # Devolver cache si coincide
        if (
            self._cache_sim is not None
            and self._cache_seed == seed
            and self._cache_n == n_simulaciones
        ):
            return self._cache_sim

        rng = np.random.default_rng(seed)

        # Muestrear frecuencias
        frecuencias = self._freq.rvs(size=n_simulaciones, random_state=rng)
        frecuencias = frecuencias.astype(int)

        # Muestrear severidades vectorizadamente
        total_siniestros = int(frecuencias.sum())
        if total_siniestros > 0:
            severidades = self._sev.rvs(size=total_siniestros, random_state=rng)
        else:
            severidades = np.array([])

        # Sumar severidades por simulacion
        perdidas = np.zeros(n_simulaciones)
        idx = 0
        for i, n in enumerate(frecuencias):
            n = int(n)
            if n > 0:
                perdidas[i] = severidades[idx : idx + n].sum()
                idx += n

        self._cache_sim = perdidas
        self._cache_seed = seed
        self._cache_n = n_simulaciones
        return perdidas

    # ------------------------------------------------------------------
    # Medidas de riesgo
    # ------------------------------------------------------------------

    def var(self, nivel: float = 0.95, n_simulaciones: int = 100_000, seed: int | None = None) -> Decimal:
        """Value at Risk al nivel de confianza dado."""
        perdidas = self.simular_perdidas(n_simulaciones=n_simulaciones, seed=seed)
        valor = float(np.quantile(perdidas, nivel))
        return Decimal(str(round(valor, 2)))

    def tvar(self, nivel: float = 0.95, n_simulaciones: int = 100_000, seed: int | None = None) -> Decimal:
        """Tail Value at Risk (CVaR / Expected Shortfall)."""
        perdidas = self.simular_perdidas(n_simulaciones=n_simulaciones, seed=seed)
        umbral = float(np.quantile(perdidas, nivel))
        cola = perdidas[perdidas >= umbral]
        if len(cola) == 0:
            return self.var(nivel=nivel, n_simulaciones=n_simulaciones, seed=seed)
        valor = float(cola.mean())
        return Decimal(str(round(valor, 2)))

    def prima_riesgo(
        self,
        nivel_confianza: float = 0.95,
        n_simulaciones: int = 100_000,
        seed: int | None = None,
    ) -> Decimal:
        """
        Prima de riesgo = prima pura + recargo de seguridad.

        El recargo se basa en el VaR de simulacion menos la prima pura.
        """
        pp = self.prima_pura()
        var_val = self.var(nivel=nivel_confianza, n_simulaciones=n_simulaciones, seed=seed)
        # La prima de riesgo es al menos la prima pura
        if var_val > pp:
            return var_val
        return pp

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------

    def estadisticas(
        self, n_simulaciones: int = 100_000, seed: int | None = None
    ) -> dict:
        """
        Resumen estadistico completo del modelo.

        Returns:
            dict con media, desviacion_estandar, asimetria, var_95, tvar_95,
            var_99, tvar_99.
        """
        perdidas = self.simular_perdidas(n_simulaciones=n_simulaciones, seed=seed)

        return {
            "prima_pura": self.prima_pura(),
            "varianza_agregada": self.varianza_agregada(),
            "desviacion_estandar": Decimal(str(round(float(perdidas.std()), 2))),
            "asimetria": Decimal(str(round(float(stats.skew(perdidas)), 4))),
            "var_95": Decimal(str(round(float(np.quantile(perdidas, 0.95)), 2))),
            "tvar_95": Decimal(
                str(round(float(perdidas[perdidas >= np.quantile(perdidas, 0.95)].mean()), 2))
            ),
            "var_99": Decimal(str(round(float(np.quantile(perdidas, 0.99)), 2))),
            "tvar_99": Decimal(
                str(round(float(perdidas[perdidas >= np.quantile(perdidas, 0.99)].mean()), 2))
            ),
            "minimo": Decimal(str(round(float(perdidas.min()), 2))),
            "maximo": Decimal(str(round(float(perdidas.max()), 2))),
            "simulaciones": n_simulaciones,
        }
