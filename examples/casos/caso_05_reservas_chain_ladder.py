"""Caso 5 - Reservas: Chain Ladder en una cartera de auto.

El caso
-------
Una aseguradora de autos cierra el ejercicio 2025 y debe constituir la
reserva de siniestros ocurridos y no pagados. Su triangulo de siniestros
PAGADOS acumulados (miles de MXN) cubre los anios de origen 2019-2024:
los siniestros de 2019 ya casi terminaron de pagarse; los de 2024 apenas
comienzan. El actuario aplica Chain Ladder para estimar el costo ultimo de
cada anio.

Que demuestra este caso
-----------------------
1. Como leer un triangulo: cada renglon es un anio de accidente, cada
   columna un anio de desarrollo; la diagonal es lo pagado a la fecha.
2. Chain Ladder: los factores de desarrollo (link ratios) proyectan cada
   renglon hasta su costo ultimo. Reserva = ultimate - pagado.
3. Las identidades duras del metodo: el ultimate NUNCA puede ser menor a lo
   ya pagado, y los factores decrecen hacia 1 conforme madura el desarrollo.
4. Que la reserva es una estimacion, no una certeza: el error estandar de
   Mack (1993) cuantifica cuanta incertidumbre aporta cada anio de origen.

Limite declarado
----------------
El error estandar de Mack mide el error de prediccion CONDICIONADO al metodo
Chain Ladder: varianza de proceso mas varianza de estimacion de los factores.
No cubre riesgo de modelo, cambio de mezcla de cartera, inflacion no observada
ni la incertidumbre de un factor de cola. El rango que reporta es
reserva +/- z*SE; Mack no supone normalidad, asi que es una escala de magnitud
y no un intervalo con cobertura exacta.

Fuentes: metodo Chain Ladder; estructura de triangulos conforme a la practica
de reservas P&C. Error de prediccion segun Mack, 1993, ASTIN Bulletin 23(2),
validado contra el triangulo de Taylor & Ashe (tests/unit/test_mack.py).
"""

from decimal import Decimal

import pandas as pd

from suite_actuarial.core.validators import ConfiguracionChainLadder, MetodoPromedio
from suite_actuarial.reservas import ChainLadder, calcular_mack

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
# 3. Error de prediccion segun Mack (1993)
# ----------------------------------------------------------------------------
mack = cl.calcular_mack(triangulo)
rango_inf, rango_sup = mack.reserve_range
print("\nError de prediccion (Mack, 1993):")
print(f"  Error estandar total:      {mack.standard_error:>12,.0f} miles MXN")
print(f"  Coef. de variacion:        {mack.coefficient_of_variation:>12.1%}")
print(f"  Rango reserva +/- 1.96 SE: [{rango_inf:,.0f} , {rango_sup:,.0f}]")
print("\n  Aporte de incertidumbre por anio de origen:")
print(f"  {'anio':>6} {'reserva':>12} {'error est.':>12} {'CV':>8}")
for anio in triangulo.index:
    print(
        f"  {anio:>6} {mack.reservas_por_anio[anio]:>12,.0f} "
        f"{mack.se_por_anio[anio]:>12,.0f} {mack.cv_por_anio[anio]:>8.1%}"
    )
print("\n  Lectura: los anios recientes concentran reserva Y error. El error")
print("  total es MAYOR que la agregacion independiente de los anuales, porque")
print("  todos los anios comparten los mismos factores estimados y sus errores")
print("  estan correlacionados: ese termino cruzado es parte del modelo.")
print("  LIMITE: mide el error CONDICIONADO al Chain Ladder. No cubre riesgo de")
print("  modelo, cambio de mezcla, inflacion no observada ni cola estimada.")

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

# d) El error de Mack es homogeneo de grado 1: multiplicar el triangulo por 100
#    multiplica el error estandar por 100 y deja el CV invariante. Es una
#    identidad del modelo (Var = sigma_k^2 * C), no una repeticion del calculo.
#    (Las aserciones anteriores -- "el error estandar es positivo" y "el rango
#    contiene a la estimacion" -- eran tautologicas: el rango se CONSTRUYE como
#    reserva +/- 1.96*SE, asi que no podian fallar. Ver docs/AUDIT.md, A9.)
mack_escalado = calcular_mack(triangulo * 100)
assert abs(mack_escalado.standard_error - 100 * mack.standard_error) < Decimal("0.01"), (
    "el error de Mack debe escalar linealmente con el volumen del triangulo"
)
assert abs(mack_escalado.coefficient_of_variation - mack.coefficient_of_variation) < Decimal(
    "0.0001"
), "el coeficiente de variacion no debe depender del nivel"

# e) El error total EXCEDE la agregacion independiente de los errores anuales.
#    Los factores f_k son comunes a todos los anios de origen, asi que sus
#    errores estan correlacionados positivamente y el termino cruzado suma. Si
#    esta desigualdad se invierte, el termino de correlacion se perdio.
agregacion_independiente = (
    sum(float(se) ** 2 for se in mack.se_por_anio.values()) ** 0.5  # noqa: S101
)
assert float(mack.standard_error) > agregacion_independiente, (
    "el error total debe exceder la raiz de la suma de cuadrados: los anios "
    "comparten los mismos factores estimados"
)

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: obtener ultimate < pagado (bug de")
print("indexado), confundir pagados con incurridos, ignorar el factor de cola")
print("y reportar la reserva como cifra exacta sin su error de estimacion.")
