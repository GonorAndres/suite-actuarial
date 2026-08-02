"""
Modelo colectivo de riesgo (collective risk model) para seguros de danos.

S = X1 + X2 + ... + XN
donde N ~ distribucion de frecuencia, Xi ~ distribucion de severidad

Este modulo es el nucleo matematico de la tarificacion de seguros de
propiedad y casualidad (P&C / danos).

El metodo es estandar; las cifras no estan respaldadas mientras los parametros
no procedan de experiencia propia. Ver `DISCLAIMER`.
"""

import warnings
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

import numpy as np
from scipy import stats

from suite_actuarial.config.schema import ValidationTier
from suite_actuarial.core.warnings import ExperimentalModelWarning

DISCLAIMER = (
    "AVISO: este modulo implementa el modelo colectivo estandar, pero sus "
    "cifras son ILUSTRATIVAS mientras los parametros no procedan de experiencia "
    "propia: no ajusta ninguna distribucion a datos, usa los parametros que se "
    "le entreguen. Supone que N y las X son independientes y que las X son "
    "identicamente distribuidas; no reconoce deducible, limite por siniestro, "
    "reaseguro, inflacion ni descuento; y trata los parametros como conocidos, "
    "de modo que sus medidas de riesgo no incorporan incertidumbre de parametro. "
    "VaR y TVaR son estimaciones Monte Carlo con error de muestreo que la "
    "respuesta no reporta: al 99% descansan sobre el 1% de las simulaciones. "
    "Para uso profesional, ajuste las distribuciones a su experiencia y reporte "
    "el error de estimacion."
)

#: Nivel de respaldo de las cifras de este modulo. Los parametros los fija quien
#: llama y no se ajustan contra experiencia alguna, asi que ninguna medida de
#: riesgo puede presentarse como respaldada.
VALIDATION_TIER = ValidationTier.EXPERIMENTAL.value

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

#: Nombres exactos de parametro que exige cada distribucion.
#:
#: Es la unica fuente de verdad de esos nombres: `ModeloColectivo` valida contra
#: ella y el borde HTTP la nombra en su 422. Las distribuciones se construyen
#: indexando el diccionario recibido (`p["lambda_"]`), asi que sin esta
#: declaracion un nombre equivocado -- `lambda` en vez de `lambda_` -- o uno
#: ausente reventaba como `KeyError` sin decir cual era el juego valido.
PARAMS_FRECUENCIA: dict[str, frozenset[str]] = {
    "poisson": frozenset({"lambda_"}),
    "negbinom": frozenset({"n", "p"}),
    "binomial": frozenset({"n", "p"}),
}

PARAMS_SEVERIDAD: dict[str, frozenset[str]] = {
    "lognormal": frozenset({"mu", "sigma"}),
    "pareto": frozenset({"alpha", "scale"}),
    "gamma": frozenset({"alpha", "beta"}),
    "weibull": frozenset({"c", "scale"}),
    "exponencial": frozenset({"lambda_"}),
}


def verificar_parametros(
    distribucion: str,
    params: Mapping[str, Any],
    requeridos: Mapping[str, frozenset[str]],
    campo: str,
) -> None:
    """Exige de `params` los nombres exactos que pide `distribucion`.

    No valida el nombre de la distribucion: si es desconocido no hay juego de
    parametros contra el cual comparar, y quien llama ya lo rechaza aparte.

    Args:
        distribucion: nombre de la distribucion elegida.
        params: parametros recibidos.
        requeridos: `PARAMS_FRECUENCIA` o `PARAMS_SEVERIDAD`.
        campo: nombre del campo que se esta validando, para el mensaje.

    Raises:
        ValueError: si falta un parametro requerido o sobra uno no reconocido.
            El mensaje nombra el juego valido en ambos casos.
    """
    esperados = requeridos.get(distribucion)
    if esperados is None:
        return

    recibidos = set(params)
    faltantes = sorted(esperados - recibidos)
    no_reconocidos = sorted(recibidos - esperados)
    if not faltantes and not no_reconocidos:
        return

    detalle = []
    if faltantes:
        detalle.append(f"faltan {faltantes}")
    if no_reconocidos:
        detalle.append(f"no se reconocen {no_reconocidos}")
    raise ValueError(
        f"{campo} de '{distribucion}': {'; '.join(detalle)}. "
        f"Los parametros de '{distribucion}' son {sorted(esperados)}."
    )


# Techo de siniestros individuales que una simulacion puede muestrear.
#
# El trabajo de `simular_perdidas` no escala con `n_simulaciones` sino con
# E[N] * n_simulaciones: la severidad se muestrea una vez por siniestro, no una
# vez por simulacion. Una frecuencia media alta convierte una peticion pequena
# en una asignacion de memoria arbitrariamente grande. El limite es de defensa,
# no actuarial: 2e7 muestras son ~160 MB en float64 y cubren cualquier corrida
# educativa razonable (1e5 simulaciones con frecuencia media 200).
MAX_SINIESTROS_SIMULADOS = 20_000_000


class ModeloColectivo:
    """
    Modelo colectivo de riesgo (collective risk model).

    S = X1 + X2 + ... + XN
    donde N ~ distribucion de frecuencia, Xi ~ distribucion de severidad

    Soporta:
        Frecuencia: poisson, negbinom, binomial
        Severidad: lognormal, pareto, gamma, weibull, exponencial

    Los nombres de parametro que exige cada distribucion estan declarados en
    `PARAMS_FRECUENCIA` y `PARAMS_SEVERIDAD`, y se validan al construir. Al
    construirse emite ademas `ExperimentalModelWarning` con `DISCLAIMER`, que
    viaja tambien en la respuesta del API: la prima pura y las medidas de riesgo
    no deben circular sin su limite.
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

        verificar_parametros(
            dist_frecuencia, params_frecuencia, PARAMS_FRECUENCIA, "params_frecuencia"
        )
        verificar_parametros(dist_severidad, params_severidad, PARAMS_SEVERIDAD, "params_severidad")

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

        # Despues de validar: una entrada invalida no produce cifra alguna, asi
        # que no hay resultado que acompanar con el aviso.
        warnings.warn(DISCLAIMER, ExperimentalModelWarning, stacklevel=2)

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

    def simular_perdidas(self, n_simulaciones: int = 10_000, seed: int | None = None) -> np.ndarray:
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

        if n_simulaciones < 1:
            raise ValueError(f"n_simulaciones debe ser al menos 1, se recibio {n_simulaciones}.")

        # El costo lo fija E[N] * n_simulaciones, no n_simulaciones. Se estima
        # antes de muestrear nada para rechazar la peticion en O(1) en vez de
        # intentar la asignacion y morir con MemoryError.
        media_frecuencia = float(self._freq.mean())
        if not np.isfinite(media_frecuencia):
            raise ValueError(
                "La distribucion de frecuencia no tiene media finita; "
                "revise los parametros antes de simular."
            )
        esperado = media_frecuencia * n_simulaciones
        if esperado > MAX_SINIESTROS_SIMULADOS:
            raise ValueError(
                f"La simulacion muestrearia del orden de {esperado:.3g} siniestros "
                f"(frecuencia media {media_frecuencia:.3g} x {n_simulaciones} "
                f"simulaciones), por encima del limite de {MAX_SINIESTROS_SIMULADOS:,}. "
                "Reduzca n_simulaciones o la frecuencia media."
            )

        rng = np.random.default_rng(seed)

        # Muestrear frecuencias
        frecuencias = self._freq.rvs(size=n_simulaciones, random_state=rng)
        frecuencias = frecuencias.astype(int)

        # Muestrear severidades vectorizadamente
        total_siniestros = int(frecuencias.sum())
        if total_siniestros > MAX_SINIESTROS_SIMULADOS:
            # Respaldo: la media pasó el filtro pero la realizacion se disparo.
            raise ValueError(
                f"La simulacion produjo {total_siniestros:,} siniestros, por encima "
                f"del limite de {MAX_SINIESTROS_SIMULADOS:,}. "
                "Reduzca n_simulaciones o la frecuencia media."
            )
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

    def var(
        self, nivel: float = 0.95, n_simulaciones: int = 100_000, seed: int | None = None
    ) -> Decimal:
        """Value at Risk al nivel de confianza dado."""
        perdidas = self.simular_perdidas(n_simulaciones=n_simulaciones, seed=seed)
        valor = float(np.quantile(perdidas, nivel))
        return Decimal(str(round(valor, 2)))

    def tvar(
        self, nivel: float = 0.95, n_simulaciones: int = 100_000, seed: int | None = None
    ) -> Decimal:
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
    ) -> dict[str, Any]:
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
