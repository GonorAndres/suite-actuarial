"""Caso 4 - Pensiones IMSS: Ley 73 vs Ley 97 y el papel de la UMA.

El caso
-------
Don Roberto se afilio al IMSS en 1990 (regimen Ley 73), tiene 1,800 semanas
cotizadas y se retira a los 65 anios con un salario promedio de las ultimas
250 semanas equivalente al tope legal de 25 UMA diarias. Su hija Sofia, en
cambio, se afilio en 2005 (Ley 97): a sus 65 anios llegara con un saldo
AFORE de $1,800,000 MXN y debera convertirlo en una renta vitalicia.

Que demuestra este caso
-----------------------
1. Como el regimen depende de la FECHA de afiliacion (antes o despues del
   1 de julio de 1997), no de la edad ni de la fecha de retiro.
2. Ley 73 es beneficio definido: porcentaje del salario promedio segun
   semanas cotizadas, con tope de 25 UMA. La UMA NO es el salario minimo:
   desde 2016 las pensiones se topan y actualizan en UMA.
3. Ley 97 es contribucion definida: el saldo AFORE compra una renta
   vitalicia cuyo monto depende de la tabla de mortalidad y la tasa tecnica.
   Identidad: prima unica = pension mensual x 12 x factor de renta (a''_x).
4. La UMA se toma de la configuracion regulatoria anual del paquete, con
   fuente oficial (INEGI/DOF), no de una constante enterrada en el codigo.

Fuentes: UMA 2026 (INEGI, vigente feb-2026 a ene-2027) via cargar_config;
porcentajes Ley 73 (Art. 167 LSS 1973); EMSSA-09 para la renta vitalicia.
"""

import warnings
from decimal import Decimal

from suite_actuarial import (
    CalculadoraIMSS,
    PensionLey73,
    PensionLey97,
    RentaVitalicia,
    TablaMortalidad,
    cargar_config,
)

# Los modelos de pensiones estan marcados como experimentales; para este
# ejemplo pedagogico silenciamos la advertencia (en produccion, atiendala).
warnings.simplefilter("ignore")

# ----------------------------------------------------------------------------
# 1. La UMA viene de la configuracion regulatoria anual (con fuente)
# ----------------------------------------------------------------------------
config = cargar_config(2026)
UMA_DIARIA = config.uma.uma_diaria  # $117.31 en 2026 (INEGI)
TOPE_25_UMA = UMA_DIARIA * 25

print("=" * 68)
print("Caso 4 - Pensiones IMSS | Ley 73 vs Ley 97")
print("=" * 68)
print(f"UMA diaria 2026:            ${UMA_DIARIA:>10,.2f} (fuente: INEGI/DOF)")
print(f"Tope salarial Ley 73 (25 UMA): ${TOPE_25_UMA:>10,.2f} diarios")

# ----------------------------------------------------------------------------
# 2. El regimen lo decide la fecha de afiliacion
# ----------------------------------------------------------------------------
imss = CalculadoraIMSS()
regimen_roberto = imss.determinar_regimen("1990-03-15")
regimen_sofia = imss.determinar_regimen("2005-08-01")
print(f"\nAfiliado en 1990 -> regimen: {regimen_roberto}")
print(f"Afiliada en 2005 -> regimen: {regimen_sofia}")

# ----------------------------------------------------------------------------
# 3. Don Roberto (Ley 73): beneficio definido con salario topado a 25 UMA
# ----------------------------------------------------------------------------
pension73 = PensionLey73(
    semanas_cotizadas=1800,
    salario_promedio_5_anos=TOPE_25_UMA,  # promedio de ultimas 250 semanas
    edad_retiro=65,
)
resumen = pension73.resumen()

print("\nDon Roberto, Ley 73 (1,800 semanas, retiro a los 65):")
print(f"  Porcentaje por semanas:  {Decimal(str(resumen['porcentaje_pension'])):.2%}")
print(f"  Pension mensual:         ${pension73.calcular_pension_mensual():>12,.2f}")
print(f"  Aguinaldo anual:         ${pension73.calcular_aguinaldo():>12,.2f}")

# ----------------------------------------------------------------------------
# 4. Sofia (Ley 97): el saldo AFORE compra una renta vitalicia
# ----------------------------------------------------------------------------
SALDO_AFORE = Decimal("1800000")
TASA_TECNICA_PENSIONES = Decimal("0.035")

tabla = TablaMortalidad.cargar_emssa09()
pension97 = PensionLey97(
    saldo_afore=SALDO_AFORE,
    edad=65,
    sexo="femenino",
    semanas_cotizadas=1300,
    tabla_mortalidad=tabla,
    tasa_interes=TASA_TECNICA_PENSIONES,
)
pension_mensual_97 = pension97.calcular_renta_vitalicia()

print("\nSofia, Ley 97 (saldo AFORE $1,800,000, retiro a los 65):")
print(f"  Renta vitalicia mensual: ${pension_mensual_97:>12,.2f}")

# Verificacion actuarial: reconstruir la anualidad con RentaVitalicia.
renta = RentaVitalicia(
    edad=65,
    sexo="femenino",
    monto_mensual=pension_mensual_97,
    tabla_mortalidad=tabla,
    tasa_interes=TASA_TECNICA_PENSIONES,
)
factor_renta = renta.calcular_factor_renta()  # a''_65 anual
prima_unica = renta.calcular_prima_unica()

print(f"  Factor de renta a''_65:  {factor_renta:>12,.4f} anios")
print(f"  Prima unica de esa renta:${prima_unica:>12,.2f}")

# ----------------------------------------------------------------------------
# 5. Chequeos actuariales
# ----------------------------------------------------------------------------
# a) Identidad de la renta vitalicia: prima unica = pension anual x a''_x.
assert abs(prima_unica - pension_mensual_97 * 12 * factor_renta) < Decimal("1.00"), (
    "prima unica != pension anual x factor de renta"
)

# b) El saldo AFORE financia exactamente esa renta (misma tabla y tasa):
#    la prima unica de la pension calculada debe reproducir el saldo.
assert abs(prima_unica - SALDO_AFORE) < SALDO_AFORE * Decimal("0.01"), (
    "la renta vitalicia debe agotar el saldo AFORE (tolerancia 1%)"
)

# c) Ley 73: la pension nunca excede el salario promedio topado.
salario_mensual_tope = TOPE_25_UMA * Decimal("30.4")
assert pension73.calcular_pension_mensual() <= salario_mensual_tope, (
    "la pension L73 no puede exceder el salario promedio topado a 25 UMA"
)

# d) UMA != salario minimo: en 2026 el minimo general (~$315/dia) es mayor
#    que la UMA; usar el minimo inflaria el tope ilegalmente.
SALARIO_MINIMO_2026 = Decimal("315.04")
assert UMA_DIARIA < SALARIO_MINIMO_2026, "la UMA y el salario minimo son unidades distintas"

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: confundir UMA con salario minimo,")
print("aplicar reglas de Ley 97 a un afiliado de Ley 73, olvidar el tope de")
print("25 UMA, y usar el ultimo salario en vez del promedio de 250 semanas.")
