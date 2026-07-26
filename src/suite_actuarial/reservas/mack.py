"""Modelo de Mack (1993): error de prediccion del Chain Ladder.

Implementa el estimador distribution-free de Mack (Thomas Mack, "Distribution-Free
Calculation of the Standard Error of Chain Ladder Reserve Estimates", *ASTIN
Bulletin* 23(2), 1993). El modelo supone:

1. `E[C(i,k+1) | C(i,1..k)] = f_k * C(i,k)`
2. `Var[C(i,k+1) | C(i,1..k)] = sigma_k^2 * C(i,k)`
3. Independencia entre anos de origen

Bajo esos supuestos el estimador insesgado de `f_k` es el factor **ponderado por
volumen**, y el error cuadratico medio de prediccion (MSEP) del ultimate de cada
ano de origen tiene forma cerrada. Este modulo calcula:

- `f_k` ponderado por volumen, por periodo de desarrollo
- `sigma_k^2` por periodo (varianza de proceso), con la extrapolacion de Mack
  para el ultimo periodo, donde no hay grados de libertad
- MSEP por ano de origen (varianza de proceso mas varianza de estimacion)
- MSEP de la reserva total, incluyendo el termino de correlacion entre anos

A diferencia de `diagnosticos.banda_dispersion_link_ratios`, que agrupa todos los
link ratios en una sola desviacion estandar, aqui la varianza se estima **dentro
de cada periodo de desarrollo**. Sobre un triangulo exactamente multiplicativo
(`C(i,j) = a_i * b_j`) todos los `sigma_k` son cero y el error estandar total es
cero, que es la respuesta correcta.

Limites vigentes:

- El modelo cuantifica el error de prediccion **dado el metodo Chain Ladder**. No
  cubre riesgo de modelo, cambios de mezcla, inflacion no observada ni el efecto
  de una cola estimada.
- La reserva que reporta es la del Chain Ladder **ponderado por volumen**. Con
  otro promedio (simple, geometrico) el error estandar de Mack no corresponde a
  esa reserva.
- No incluye factor de cola: el ultimate es el de la ultima columna observada.
"""

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd

from suite_actuarial.reservas.triangulo import (
    factores_volumen_ponderado,
    obtener_ultima_diagonal,
    validar_triangulo,
)

#: Nombre del metodo reportado en los resultados.
METODO_MACK = "mack-1993"


@dataclass(frozen=True)
class ResultadoMack:
    """Reserva Chain Ladder ponderada por volumen con su error de prediccion.

    `standard_error` es la raiz del MSEP de la reserva total segun Mack (1993),
    e incluye el termino de correlacion entre anos de origen. No es la suma de
    los errores por ano: los estimadores `f_k` son comunes a todos los anos, asi
    que sus errores estan correlacionados positivamente.

    `reserve_range` es `reserva +/- z * SE`. Mack no supone normalidad, asi que
    ese rango es una escala de magnitud, no un intervalo con cobertura exacta;
    la distribucion de la reserva es asimetrica a la derecha.
    """

    factores_desarrollo: list[Decimal]
    sigmas: list[Decimal]
    ultimates_por_anio: dict[int, Decimal]
    reservas_por_anio: dict[int, Decimal]
    se_por_anio: dict[int, Decimal]
    cv_por_anio: dict[int, Decimal]
    reserva_total: Decimal
    standard_error: Decimal
    coefficient_of_variation: Decimal
    reserve_range: tuple[Decimal, Decimal]
    method: str = METODO_MACK


def _factores_y_sigmas(
    valores: np.ndarray,
) -> tuple[list[float], list[float], list[float]]:
    """Calcula `f_k`, `sigma_k^2` y el volumen `S_k` por periodo de desarrollo.

    Para el periodo `k` (de la columna k a la k+1) se usan las filas donde ambas
    celdas estan observadas:

        f_k     = sum_i C(i,k+1) / sum_i C(i,k)
        S_k     = sum_i C(i,k)
        sigma_k^2 = 1/(I_k - 1) * sum_i C(i,k) * (C(i,k+1)/C(i,k) - f_k)^2

    Con `I_k = 1` no hay grados de libertad. Mack propone entonces

        sigma_k^2 = min(sigma_{k-1}^4 / sigma_{k-2}^2,
                        min(sigma_{k-1}^2, sigma_{k-2}^2))

    que extrapola la tendencia decreciente de la varianza sin permitir que crezca.
    """
    n_cols = valores.shape[1]
    factores, volumenes = factores_volumen_ponderado(valores)
    sigmas2: list[float] = []
    pendientes: list[int] = []

    for k in range(n_cols - 1):
        actual = valores[:, k]
        siguiente = valores[:, k + 1]
        mask = ~np.isnan(actual) & ~np.isnan(siguiente) & (actual > 0)
        n_obs = int(mask.sum())

        if n_obs == 0:
            sigmas2.append(0.0)
            continue

        c_k = actual[mask]
        c_k1 = siguiente[mask]
        f_k = factores[k]

        if n_obs >= 2:
            ratios = c_k1 / c_k
            sigmas2.append(float((c_k * (ratios - f_k) ** 2).sum() / (n_obs - 1)))
        else:
            # Sin grados de libertad: se resuelve tras conocer los anteriores.
            sigmas2.append(float("nan"))
            pendientes.append(k)

    for k in pendientes:
        if k >= 2 and sigmas2[k - 2] > 0 and not np.isnan(sigmas2[k - 1]):
            sigmas2[k] = min(
                sigmas2[k - 1] ** 2 / sigmas2[k - 2],
                min(sigmas2[k - 1], sigmas2[k - 2]),
            )
        elif k >= 1 and not np.isnan(sigmas2[k - 1]):
            # Un solo periodo previo disponible: se repite, sin extrapolar.
            sigmas2[k] = sigmas2[k - 1]
        else:
            sigmas2[k] = 0.0

    return factores, sigmas2, volumenes


def _proyectar(valores: np.ndarray, factores: list[float]) -> np.ndarray:
    """Completa el triangulo hacia adelante con los factores ponderados."""
    proyectado = valores.copy()
    n_rows, n_cols = proyectado.shape

    for i in range(n_rows):
        observados = np.where(~np.isnan(proyectado[i]))[0]
        if len(observados) == 0:
            continue
        ultima = int(observados[-1])
        for j in range(ultima + 1, n_cols):
            proyectado[i, j] = proyectado[i, j - 1] * factores[j - 1]

    return proyectado


def calcular_mack(
    triangulo: pd.DataFrame,
    *,
    confidence_z: Decimal = Decimal("1.96"),
    permitir_desarrollo_negativo: bool = False,
) -> ResultadoMack:
    """Calcula la reserva Chain Ladder y su error de prediccion segun Mack (1993).

    Args:
        triangulo: Triangulo acumulado de siniestros
        confidence_z: Multiplicador para `reserve_range` (no es una cobertura)
        permitir_desarrollo_negativo: Admite celdas acumuladas negativas
            (recuperaciones). Debe coincidir con lo declarado en la
            configuracion del metodo: sin este parametro la validacion de aqui
            rechazaba un triangulo que `ChainLadder.calcular` si aceptaba, y el
            mensaje pedia activar una bandera que esta funcion no recibia.

            Advertencia: el estimador se mantiene finito y con error estandar
            no negativo bajo desarrollo negativo moderado (comprobado hasta
            f_k del orden de 1e-3), pero `sigma_k^2` se estima solo sobre las
            filas con `C(i,k) > 0`; las celdas acumuladas no positivas quedan
            fuera de esa estimacion sin aviso, asi que el error estandar puede
            apoyarse en menos observaciones de las que aparenta.

    Returns:
        ResultadoMack con factores, sigmas, reservas y errores por ano y total

    Raises:
        ValueError: si el triangulo esta vacio o tiene menos de dos periodos de
            desarrollo, en cuyo caso no hay ningun factor que estimar
    """
    validar_triangulo(triangulo, permitir_desarrollo_negativo=permitir_desarrollo_negativo)

    if triangulo.shape[1] < 2:
        raise ValueError("Mack requiere al menos dos periodos de desarrollo")

    valores = triangulo.to_numpy(dtype=float)
    n_rows, n_cols = valores.shape

    factores, sigmas2, volumenes = _factores_y_sigmas(valores)
    proyectado = _proyectar(valores, factores)

    diagonal = obtener_ultima_diagonal(triangulo)
    ultimo_observado = {}
    for i in range(n_rows):
        observados = np.where(~np.isnan(valores[i]))[0]
        ultimo_observado[i] = int(observados[-1]) if len(observados) else -1

    # MSEP por ano de origen (Mack 1993, teorema 3):
    #   mse(C_i,ult) = C_i,ult^2 * sum_k (sigma_k^2 / f_k^2) * (1/C_i,k + 1/S_k)
    # El primer termino es varianza de proceso; el segundo, varianza de
    # estimacion de f_k. La suma corre desde la ultima columna observada del ano.
    mse_por_fila: dict[int, float] = {}
    for i in range(n_rows):
        inicio = ultimo_observado[i]
        if inicio < 0 or inicio >= n_cols - 1:
            mse_por_fila[i] = 0.0
            continue

        ultimate = proyectado[i, n_cols - 1]
        acumulado = 0.0
        for k in range(inicio, n_cols - 1):
            c_ik = proyectado[i, k]
            f_k = factores[k]
            s_k = volumenes[k]
            if f_k <= 0 or c_ik <= 0 or s_k <= 0:
                continue
            acumulado += (sigmas2[k] / f_k**2) * (1.0 / c_ik + 1.0 / s_k)
        mse_por_fila[i] = ultimate**2 * acumulado

    # MSEP de la reserva total: suma de los MSEP individuales mas el termino de
    # correlacion, que aparece porque todos los anos comparten los mismos f_k.
    #   2 * C_i,ult * (sum_{j>i} C_j,ult) * sum_k (sigma_k^2 / f_k^2) / S_k
    mse_total = sum(mse_por_fila.values())
    for i in range(n_rows):
        inicio = ultimo_observado[i]
        if inicio < 0 or inicio >= n_cols - 1:
            continue
        posteriores = sum(
            proyectado[j, n_cols - 1] for j in range(i + 1, n_rows) if ultimo_observado[j] >= 0
        )
        if posteriores <= 0:
            continue
        acumulado = 0.0
        for k in range(inicio, n_cols - 1):
            f_k = factores[k]
            s_k = volumenes[k]
            if f_k <= 0 or s_k <= 0:
                continue
            acumulado += 2.0 * (sigmas2[k] / f_k**2) / s_k
        mse_total += proyectado[i, n_cols - 1] * posteriores * acumulado

    ultimates: dict[int, Decimal] = {}
    reservas: dict[int, Decimal] = {}
    se_por_anio: dict[int, Decimal] = {}
    cv_por_anio: dict[int, Decimal] = {}

    for i in range(n_rows):
        anio = int(triangulo.index[i])
        ultimate = float(proyectado[i, n_cols - 1])
        pagado = float(diagonal.get(triangulo.index[i], 0.0))
        reserva = ultimate - pagado
        se = float(np.sqrt(max(mse_por_fila[i], 0.0)))

        ultimates[anio] = Decimal(str(ultimate))
        reservas[anio] = Decimal(str(reserva))
        se_por_anio[anio] = Decimal(str(se))
        cv_por_anio[anio] = Decimal(str(se / reserva)) if reserva > 0 else Decimal("0")

    reserva_total = sum(reservas.values(), Decimal("0"))
    se_total = Decimal(str(float(np.sqrt(max(mse_total, 0.0)))))
    cv_total = (se_total / reserva_total) if reserva_total > 0 else Decimal("0")

    return ResultadoMack(
        factores_desarrollo=[Decimal(str(f)) for f in factores],
        sigmas=[Decimal(str(float(np.sqrt(max(s, 0.0))))) for s in sigmas2],
        ultimates_por_anio=ultimates,
        reservas_por_anio=reservas,
        se_por_anio=se_por_anio,
        cv_por_anio=cv_por_anio,
        reserva_total=reserva_total,
        standard_error=se_total,
        coefficient_of_variation=cv_total,
        reserve_range=(
            max(Decimal("0"), reserva_total - confidence_z * se_total),
            reserva_total + confidence_z * se_total,
        ),
    )
