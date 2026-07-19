"""Caso 5 - Reservas: Chain Ladder con incertidumbre de Mack (cartera de auto).

El caso
-------
Una aseguradora de autos cierra el ejercicio 2025 y debe constituir la
reserva de siniestros ocurridos y no pagados. Su triangulo de siniestros
PAGADOS acumulados (miles de MXN) cubre los anios de origen 2019-2024:
los siniestros de 2019 ya casi terminaron de pagarse; los de 2024 apenas
comienzan. El actuario aplica Chain Ladder para estimar el costo ultimo de
cada anio y Mack para medir que tan incierta es esa estimacion.

Que demuestra este caso
-----------------------
1. Como leer un triangulo: cada renglon es un anio de accidente, cada
   columna un anio de desarrollo; la diagonal es lo pagado a la fecha.
2. Chain Ladder: los factores de desarrollo (link ratios) proyectan cada
   renglon hasta su costo ultimo. Reserva = ultimate - pagado.
3. Las identidades duras del metodo: el ultimate NUNCA puede ser menor a lo
   ya pagado, y los factores decrecen hacia 1 conforme madura el desarrollo.
4. Mack: los anios recientes (menos desarrollados) cargan mas error de
   estimacion; la reserva es una estimacion, no una certeza.

Fuentes: metodo Chain Ladder y modelo de Mack (Mack, 1993, ASTIN Bulletin);
estructura de triangulos conforme a la practica de reservas P&C.
"""

from decimal import Decimal

import pandas as pd

from suite_actuarial.core.validators import ConfiguracionChainLadder, MetodoPromedio
from suite_actuarial.reservas import ChainLadder

# ----------------------------------------------------------------------------
# 1. Triangulo de siniestros pagados acumulados (miles de MXN)
#    Renglon = anio de origen (accidente); columna = anio de desarrollo.
# ----------------------------------------------------------------------------
triangulo = pd.DataFrame(
    {
        1: [12480, 13650, 14820, 16090, 17510, 18930],
        2: [18720, 20475, 22230, 24135, 26265, None],
        3: [21580, 23600, 25640, 27830, None, None],
        4: [23090, 25250, 27430, None, None, None],
        5: [23780, 26010, None, None, None, None],
        6: [24020, None, None, None, None, None],
    },
    index=[2019, 2020, 2021, 2022, 2023, 2024],
)

print("=" * 68)
print("Caso 5 - Reserva de siniestros auto | Chain Ladder + Mack")
print("=" * 68)
print("Triangulo de pagados acumulados (miles MXN):")
print(triangulo.to_string())

# ----------------------------------------------------------------------------
# 2. Chain Ladder
# ----------------------------------------------------------------------------
cl = ChainLadder(ConfiguracionChainLadder(metodo_promedio=MetodoPromedio.PONDERADO))
resultado = cl.calcular(triangulo)

print("\nFactores de desarrollo (promedio ponderado):")
factores = resultado.factores_desarrollo or []
for j, f in enumerate(factores, start=1):
    print(f"  {j} -> {j + 1}: {f:.4f}")

print("\nUltimate y reserva por anio de origen (miles MXN):")
print(f"  {'anio':>6} {'pagado':>12} {'ultimate':>12} {'reserva':>12}")
diagonal = {anio: triangulo.loc[anio].dropna().iloc[-1] for anio in triangulo.index}
for anio in triangulo.index:
    ult = resultado.ultimates_por_anio[anio]
    res = resultado.reservas_por_anio[anio]
    print(f"  {anio:>6} {diagonal[anio]:>12,.0f} {ult:>12,.0f} {res:>12,.0f}")

print(f"\n  Reserva total (IBNR + casos): {resultado.reserva_total:>12,.0f} miles MXN")

# ----------------------------------------------------------------------------
# 3. Incertidumbre de Mack
# ----------------------------------------------------------------------------
mack = cl.calcular_mack(triangulo)
rango_inf, rango_sup = mack.reserve_range
print("\nIncertidumbre de Mack (aproximacion) sobre la reserva total:")
print(f"  Error estandar:            {mack.standard_error:>12,.0f} miles MXN")
print(f"  Coef. de variacion:        {mack.coefficient_of_variation:>12.1%}")
print(f"  Rango razonable de reserva:[{rango_inf:,.0f} , {rango_sup:,.0f}]")
print("  Lectura: la reserva es una ESTIMACION; los anios recientes (2023,")
print("  2024) aportan la mayor parte de la reserva y de la incertidumbre.")

# ----------------------------------------------------------------------------
# 4. Chequeos actuariales
# ----------------------------------------------------------------------------
# a) Ultimate >= pagado a la fecha, renglon por renglon (chequeo duro).
for anio in triangulo.index:
    assert resultado.ultimates_por_anio[anio] >= Decimal(str(diagonal[anio])), (
        f"ultimate < pagado en {anio}: el triangulo esta mal indexado"
    )

# b) Reserva total = suma(ultimate - pagado) y nunca negativa.
assert resultado.reserva_total == sum(resultado.reservas_por_anio.values()), (
    "la reserva total debe ser la suma por anio"
)
assert resultado.reserva_total >= 0, "IBNR negativo: revisar datos"

# c) Los factores de desarrollo decrecen hacia 1 (el desarrollo madura).
assert all(f >= 1 for f in factores), "un factor < 1 en pagados acumulados es anomalo"
assert factores == sorted(factores, reverse=True), "los factores deben decrecer hacia 1"

# d) Mack: hay incertidumbre positiva y el rango encierra a la mejor estimacion.
assert mack.standard_error > 0, "el error estandar de Mack debe ser positivo"
assert rango_inf <= resultado.reserva_total <= rango_sup, (
    "el rango de Mack debe contener la mejor estimacion de la reserva"
)

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: obtener ultimate < pagado (bug de")
print("indexado), confundir pagados con incurridos, ignorar el factor de cola")
print("y reportar la reserva como cifra exacta sin su error de estimacion.")
