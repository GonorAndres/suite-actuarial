"""Estimacion del factor de cola por curva de potencia inversa (Sherman, 1984).

El triangulo observa el desarrollo hasta el ultimo periodo con datos. El factor
de cola representa el desarrollo posterior a ese punto. Repetir el ultimo factor
observado no lo estima: supone que la maduracion se detiene justo donde termina
la observacion, lo que contradice el patron decreciente del propio triangulo
(hallazgo A10 de `docs/AUDIT.md`).

Metodo implementado — Richard Sherman, "Extrapolating, Smoothing and
Interpolating Development Factors", *PCAS* LXXI, 1984: el exceso del factor
sobre la unidad decae como una potencia del periodo de desarrollo,

    f_k - 1 = a * k^(-b),      a > 0,  b > 0

que en escala logaritmica es una recta,

    ln(f_k - 1) = ln(a) - b * ln(k)

y se ajusta por minimos cuadrados sobre los factores observados. El factor de
cola es el producto de los factores extrapolados mas alla del ultimo periodo
observado, truncado en un horizonte explicito:

    cola = prod_{k=K+1}^{K+H} (1 + a * k^(-b))

Limites que el metodo no resuelve:

- Es **extrapolacion**: ningun dato del triangulo respalda el desarrollo mas
  alla del ultimo periodo observado. El ajuste solo garantiza que la cola sea
  coherente con la tendencia observada, no que sea correcta.
- Con `b <= 1` la serie no converge: la cola depende materialmente del horizonte
  de truncamiento, y eso se reporta y se avisa.
- La bondad del ajuste (`r_cuadrado`) es un diagnostico obligatorio de lectura:
  un ajuste pobre significa que el patron no es una potencia inversa y que la
  cola deberia declararse a mano o tomarse de un benchmark documentado.
"""

import math
import warnings
from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from suite_actuarial.core.warnings import ExperimentalModelWarning

#: Horizonte de extrapolacion por omision, en periodos de desarrollo.
HORIZONTE_POR_OMISION = 100

#: Un factor por debajo de este umbral se considera desarrollo terminado.
TOLERANCIA_DESARROLLO = 1e-9

#: Metodos reportados en `AjusteCola.metodo`.
METODO_SHERMAN = "sherman_curva_potencia_inversa"
METODO_SIN_DESARROLLO = "sin_desarrollo_residual"

DISCLAIMER_EXTRAPOLACION = (
    "AVISO: el factor de cola es EXTRAPOLACION. La curva de potencia inversa de "
    "Sherman (1984) se ajusta a los factores observados y se proyecta mas alla "
    "del ultimo periodo con datos; ningun dato del triangulo respalda ese tramo. "
    "Revise la bondad del ajuste (r_cuadrado) y el horizonte de truncamiento "
    "antes de usar la cifra."
)


@dataclass(frozen=True)
class AjusteCola:
    """Resultado del ajuste de cola, con su diagnostico.

    `tail` es el producto de los factores extrapolados. `a` y `b` son los
    parametros de la curva. `r_cuadrado` es la bondad del ajuste log-log: mide
    si el patron observado se parece a una potencia inversa, no si la cola es
    correcta. `converge` indica si la serie converge (`b > 1`); si no, `tail`
    depende del horizonte y debe leerse junto con `horizonte`.
    """

    tail: Decimal
    metodo: str
    a: Decimal
    b: Decimal
    r_cuadrado: Decimal
    horizonte: int
    periodos_ajustados: int
    converge: bool


def _sin_desarrollo(horizonte: int) -> AjusteCola:
    """Desarrollo terminado: la cola es exactamente 1, sin extrapolar nada."""
    return AjusteCola(
        tail=Decimal("1"),
        metodo=METODO_SIN_DESARROLLO,
        a=Decimal("0"),
        b=Decimal("0"),
        r_cuadrado=Decimal("1"),
        horizonte=horizonte,
        periodos_ajustados=0,
        converge=True,
    )


def estimar_tail_sherman(
    factores: list[Decimal],
    *,
    horizonte: int = HORIZONTE_POR_OMISION,
) -> AjusteCola:
    """Estima el factor de cola ajustando la curva de potencia inversa.

    Args:
        factores: Factores age-to-age promedio, en orden de desarrollo. El
            primero corresponde al periodo 1 (de la columna 1 a la 2).
        horizonte: Periodos de desarrollo adicionales a extrapolar. El producto
            se trunca ahi, y el valor se reporta en el resultado.

    Returns:
        AjusteCola con la cola estimada y su diagnostico. Si el desarrollo ya
        termino (el ultimo factor observado es 1) devuelve cola 1 sin ajustar
        curva alguna: reconocerlo es parte de la estimacion.

    Raises:
        ValueError: si no hay al menos tres factores mayores que 1 con los que
            ajustar la curva, o si el ajuste da una potencia no decreciente
            (`b <= 0`). En ambos casos extrapolar fabricaria desarrollo sin
            base; corresponde declarar la cola a mano o tomarla de un benchmark.
    """
    if horizonte < 1:
        raise ValueError("El horizonte de extrapolacion debe ser al menos 1 periodo")

    if not factores:
        raise ValueError("No hay factores de desarrollo con los que estimar la cola")

    # Desarrollo terminado: el ultimo factor observado no aporta desarrollo.
    if float(factores[-1]) <= 1.0 + TOLERANCIA_DESARROLLO:
        return _sin_desarrollo(horizonte)

    periodos = []
    excesos = []
    for indice, factor in enumerate(factores, start=1):
        exceso = float(factor) - 1.0
        if exceso > TOLERANCIA_DESARROLLO:
            periodos.append(indice)
            excesos.append(exceso)

    if len(periodos) < 3:
        raise ValueError(
            f"Se necesitan al menos 3 factores mayores que 1 para ajustar la curva "
            f"de Sherman; hay {len(periodos)}. Declare `tail_factor` explicito con "
            f"su justificacion o use un benchmark documentado."
        )

    log_k = np.log(np.array(periodos, dtype=float))
    log_exceso = np.log(np.array(excesos, dtype=float))

    pendiente, intercepto = np.polyfit(log_k, log_exceso, 1)
    b = -float(pendiente)
    a = float(np.exp(intercepto))

    if b <= 0:
        raise ValueError(
            f"El ajuste da b = {b:.4f} <= 0: los factores observados no decrecen "
            f"como una potencia inversa, asi que extrapolarlos fabricaria "
            f"desarrollo creciente. Declare `tail_factor` explicito."
        )

    ajustado = intercepto + pendiente * log_k
    residual = float(np.sum((log_exceso - ajustado) ** 2))
    total = float(np.sum((log_exceso - log_exceso.mean()) ** 2))
    r2 = 1.0 - residual / total if total > 0 else 1.0

    ultimo_periodo = len(factores)
    log_tail = 0.0
    for k in range(ultimo_periodo + 1, ultimo_periodo + horizonte + 1):
        log_tail += math.log1p(a * k**-b)
    tail = math.exp(log_tail)

    converge = b > 1.0
    if not converge:
        warnings.warn(
            f"La curva ajustada tiene b = {b:.4f} <= 1: la serie de factores no "
            f"converge, asi que el factor de cola ({tail:.6f}) depende del "
            f"horizonte de truncamiento ({horizonte} periodos). No lo lea como un "
            f"limite; declare el horizonte junto con la cifra.",
            ExperimentalModelWarning,
            stacklevel=2,
        )

    return AjusteCola(
        tail=Decimal(str(tail)),
        metodo=METODO_SHERMAN,
        a=Decimal(str(a)),
        b=Decimal(str(b)),
        r_cuadrado=Decimal(str(r2)),
        horizonte=horizonte,
        periodos_ajustados=len(periodos),
        converge=converge,
    )
