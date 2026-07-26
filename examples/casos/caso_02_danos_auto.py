"""Caso 2 - Danios: cotizacion de automovil y modelo frecuencia-severidad.

El caso
-------
Miguel, 40 anios, asegura su sedan mediano 2023 con valor factura de
$420,000 MXN en la zona norte de la CDMX, cobertura amplia, deducible del 5%
sobre danios materiales. Tiene tres anios de historial con un solo siniestro.
El actuario de la aseguradora tarifica con factores tipo AMIS y ademas
modela la perdida agregada de la cartera con un modelo colectivo
Poisson-lognormal.

Que demuestra este caso
-----------------------
1. La prima pura (o de riesgo) nace de frecuencia x severidad:
   E[S] = E[N] * E[X]. Todo lo demas (recargos, comisiones) se construye
   encima de ella.
2. El efecto real del deducible: subir el deducible del 5% al 10% BAJA la
   prima, porque la aseguradora deja de pagar los siniestros pequenios.
3. La diferencia entre la suma asegurada (valor del auto) y la prima
   (lo que cuesta transferir el riesgo un anio).
4. Como el historial de siniestros ajusta la prima via bonus-malus.

Fuentes: factores de zona y grupo vehicular de referencia tipo AMIS
(ilustrativos, en el paquete); modelo colectivo estandar de la teoria del
riesgo (Klugman, Loss Models).
"""

import math
from decimal import Decimal

from suite_actuarial.danos import ModeloColectivo, SeguroAuto

# ----------------------------------------------------------------------------
# 1. Supuestos del caso
# ----------------------------------------------------------------------------
VALOR_AUTO = Decimal("420000")  # suma asegurada de danios materiales, MXN

auto = SeguroAuto(
    valor_vehiculo=VALOR_AUTO,
    tipo_vehiculo="sedan_mediano",
    antiguedad_anos=3,
    zona="cdmx_norte",
    edad_conductor=40,
    deducible_pct=Decimal("0.05"),
)

cotizacion = auto.generar_cotizacion(historial_siniestros=[0, 1, 0])

print("=" * 68)
print("Caso 2 - Auto amplia | sedan mediano $420,000 | CDMX norte")
print("=" * 68)
print("Prima por cobertura (deducible 5%):")
for cobertura, prima in auto.calcular_tarifa().items():
    print(f"  {cobertura.value:<20} ${prima:>12,.2f}")
print(f"Prima total cotizada (con bonus-malus): ${cotizacion['prima_total']:>12,.2f} MXN")

# ----------------------------------------------------------------------------
# 2. Efecto del deducible: 5% vs 10%
# ----------------------------------------------------------------------------
auto_ded10 = SeguroAuto(
    valor_vehiculo=VALOR_AUTO,
    tipo_vehiculo="sedan_mediano",
    antiguedad_anos=3,
    zona="cdmx_norte",
    edad_conductor=40,
    deducible_pct=Decimal("0.10"),
)
prima_ded05 = auto.calcular_prima_total()
prima_ded10 = auto_ded10.calcular_prima_total()

print("\nEfecto del deducible sobre la prima total (sin bonus-malus):")
print(f"  deducible  5% (${VALOR_AUTO * Decimal('0.05'):>10,.0f}): ${prima_ded05:>12,.2f}")
print(f"  deducible 10% (${VALOR_AUTO * Decimal('0.10'):>10,.0f}): ${prima_ded10:>12,.2f}")

# ----------------------------------------------------------------------------
# 3. Modelo colectivo de la cartera: frecuencia x severidad
# ----------------------------------------------------------------------------
# Cartera de autos similares: frecuencia Poisson con lambda = 0.18 siniestros
# por poliza-anio; severidad lognormal con media ~$35,000 MXN por siniestro.
# Para una lognormal, E[X] = exp(mu + sigma^2 / 2).
MU, SIGMA = 10.24, 0.60  # E[X] = exp(10.24 + 0.18) = ~$33,448
modelo = ModeloColectivo(
    dist_frecuencia="poisson",
    params_frecuencia={"lambda_": 0.18},
    dist_severidad="lognormal",
    params_severidad={"mu": MU, "sigma": SIGMA},
)

prima_pura = modelo.prima_pura()
severidad_esperada = Decimal(str(round(math.exp(MU + SIGMA**2 / 2), 2)))
frecuencia = Decimal("0.18")

print("\nModelo colectivo Poisson-lognormal (por poliza de la cartera):")
print(f"  Frecuencia esperada E[N]:      {frecuencia} siniestros/anio")
print(f"  Severidad esperada E[X]:       ${severidad_esperada:>12,.2f}")
print(f"  Prima pura E[S] = E[N]xE[X]:   ${prima_pura:>12,.2f}")
stats = modelo.estadisticas(n_simulaciones=50_000, seed=2026)
print(f"  VaR 99% de la perdida anual:   ${stats['var_99']:>12,.2f}")

# ----------------------------------------------------------------------------
# 4. Chequeos actuariales
# ----------------------------------------------------------------------------
# a) La prima pura ES frecuencia por severidad (identidad del modelo colectivo).
assert abs(prima_pura - frecuencia * severidad_esperada) < Decimal("1.00"), (
    "Prima pura != E[N] x E[X]"
)

# b) Monotonia del deducible: mas deducible, menos prima.
assert prima_ded10 < prima_ded05, "Subir el deducible debe bajar la prima"

# c) La prima es una fraccion pequenia de la suma asegurada (orden de magnitud).
assert cotizacion["prima_total"] < VALOR_AUTO * Decimal("0.10"), (
    "La prima anual no debe acercarse al valor del auto"
)

# d) La cola importa: el VaR 99% excede por mucho la perdida esperada.
assert stats["var_99"] > prima_pura * 2, "El VaR 99% debe superar con holgura a E[S]"

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: confundir suma asegurada con")
print("prima, tratar el deducible como monto fijo en vez de % de la SA, y")
print("tarificar solo con la perdida esperada ignorando la cola (VaR).")
