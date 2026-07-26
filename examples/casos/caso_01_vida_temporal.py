"""Caso 1 - Vida: seguro temporal a 20 anios para una mujer de 32 anios.

El caso
-------
Ana, 32 anios, no fumadora, contrata un seguro temporal a 20 anios con suma
asegurada de $1,500,000 MXN para proteger a su familia mientras termina de
pagar su casa. La aseguradora tarifica con la tabla EMSSA-09 (mujeres) y una
tasa tecnica del 5.5% anual, prima anual nivelada pagada por anticipado.

Que demuestra este caso
-----------------------
1. El principio de equivalencia: el valor actual de las primas que cobrara la
   aseguradora es igual al valor actual de los beneficios que promete pagar,
   es decir  P * a''(32:20) = SA * A(32:20).
2. La diferencia entre prima neta (solo riesgo) y prima de tarifa (riesgo mas
   recargos de gastos y utilidad). Nunca son iguales; la de tarifa es mayor.
3. El perfil de la reserva matematica de una temporal: arranca en cero,
   crece y regresa a cero al vencimiento, porque el producto no promete
   nada si la asegurada sobrevive (no hay componente de ahorro).

Fuentes: tabla EMSSA-09 (CNSF, experiencia mexicana de seguridad social,
incluida en el paquete con estatus ilustrativo); tasa tecnica 5.5% dentro del
rango historico regulado por la CNSF (4%-6%).

Nota: este ejemplo es una base pedagogica y de desarrollo, no una nota
tecnica registrable ante la CNSF.
"""

from decimal import Decimal

from suite_actuarial import Asegurado, ConfiguracionProducto, TablaMortalidad, VidaTemporal
from suite_actuarial.actuarial.pricing.vida_pricing import (
    calcular_anualidad,
    calcular_seguro_vida,
)
from suite_actuarial.core.models.common import Sexo

# ----------------------------------------------------------------------------
# 1. Supuestos del caso (cambie estas variables para adaptarlo a su proyecto)
# ----------------------------------------------------------------------------
EDAD = 32
SEXO = Sexo.MUJER
SUMA_ASEGURADA = Decimal("1500000")  # MXN
PLAZO = 20  # anios
TASA_TECNICA = Decimal("0.055")  # 5.5% anual

tabla = TablaMortalidad.cargar_emssa09()

config = ConfiguracionProducto(
    nombre_producto="Temporal 20 anios",
    plazo_years=PLAZO,
    tasa_interes_tecnico=TASA_TECNICA,
    recargo_gastos_admin=Decimal("0.05"),  # 5% administracion
    recargo_gastos_adq=Decimal("0.10"),  # 10% adquisicion (comision)
    recargo_utilidad=Decimal("0.03"),  # 3% utilidad
)

producto = VidaTemporal(config, tabla)
ana = Asegurado(edad=EDAD, sexo=SEXO, suma_asegurada=SUMA_ASEGURADA)

# ----------------------------------------------------------------------------
# 2. Prima: neta (riesgo puro) y de tarifa (lo que paga la asegurada)
# ----------------------------------------------------------------------------
resultado = producto.calcular_prima(ana, frecuencia_pago="anual")

print("=" * 68)
print("Caso 1 - Vida temporal 20 anios | mujer 32 anios | SA $1,500,000")
print("=" * 68)
print(f"Prima neta anual (riesgo puro):    ${resultado.prima_neta:>12,.2f} MXN")
print(f"Prima de tarifa anual (con cargos):${resultado.prima_total:>12,.2f} MXN")
print("Desglose de recargos:")
for concepto, monto in resultado.desglose_recargos.items():
    print(f"  {concepto:<24} ${monto:>12,.2f}")

# ----------------------------------------------------------------------------
# 3. Principio de equivalencia: P * a''(32:20) = SA * A(32:20)
# ----------------------------------------------------------------------------
# A(32:20): valor actual actuarial de pagar $1 al fallecer dentro del plazo.
# a''(32:20): valor actual de una anualidad anticipada de $1 mientras viva.
A_32_20 = calcular_seguro_vida(tabla, EDAD, SEXO, PLAZO, TASA_TECNICA)
a_dobleprima = calcular_anualidad(tabla, EDAD, SEXO, PLAZO, TASA_TECNICA, pago_anticipado=True)

va_primas = resultado.prima_neta * a_dobleprima
va_beneficios = SUMA_ASEGURADA * A_32_20

print("\nPrincipio de equivalencia en t=0:")
print(f"  VA(primas)     = P x a''    = ${va_primas:>14,.2f}")
print(f"  VA(beneficios) = SA x A     = ${va_beneficios:>14,.2f}")

# ----------------------------------------------------------------------------
# 4. Perfil de la reserva matematica
# ----------------------------------------------------------------------------
print("\nReserva matematica por anio de vigencia (prima nivelada):")
reservas = {t: producto.calcular_reserva(ana, anio=t) for t in (0, 5, 10, 15, 20)}
for t, v in reservas.items():
    print(f"  t={t:>2}: ${v:>12,.2f}")

# ----------------------------------------------------------------------------
# 5. Chequeos actuariales (identidades que DEBEN cumplirse)
# ----------------------------------------------------------------------------
# a) Equivalencia: VA de primas = VA de beneficios (tolerancia por redondeo).
assert abs(va_primas - va_beneficios) < Decimal("1.00"), "Fallo el principio de equivalencia"

# b) La prima de tarifa siempre excede a la prima neta.
assert resultado.prima_total > resultado.prima_neta, "La tarifa debe superar a la prima neta"

# c) Reserva inicial ~ 0 con prima nivelada, y regresa a 0 al vencimiento
#    (una temporal no promete nada por supervivencia).
assert abs(reservas[0]) < Decimal("1.00"), "La reserva en t=0 debe ser ~0 con prima nivelada"
assert abs(reservas[20]) < Decimal("1.00"), "La reserva de una temporal debe extinguirse en t=n"

# d) La reserva intermedia es positiva: la prima nivelada cobra de mas en los
#    primeros anios (mortalidad baja) para financiar los ultimos (mortalidad alta).
assert reservas[10] > 0, "La reserva intermedia de una temporal nivelada es positiva"

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: confundir prima neta con prima de")
print("tarifa, usar anualidad vencida cuando la prima es anticipada, y esperar")
print("que una temporal acumule valor de rescate como si fuera un dotal.")
