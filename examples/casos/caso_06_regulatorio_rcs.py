"""Caso 6 - Regulatorio: RCS didactico y parametros anuales con fuente.

El caso
-------
Una aseguradora mediana mexicana opera vida individual y autos. Al cierre
del ejercicio su actuario estima (con el modelo DIDACTICO del paquete, no
con la formula general certificada de la CUSF) el Requerimiento de Capital
de Solvencia por modulos: suscripcion de vida, suscripcion de danios y
riesgo de inversion, agregados con correlaciones. Cuenta con capital
disponible de $350,000,000 MXN y quiere saber si cubre el requerimiento.

Que demuestra este caso
-----------------------
1. La logica de solvencia: capital disponible vs requerimiento de capital.
   Aqui el indicador del paquete es ratio = RCS / capital, de modo que
   ratio <= 1 significa "cubierto"; la cobertura clasica es su inverso.
2. El beneficio de diversificacion: el RCS total agregado con correlaciones
   es MENOR que la suma de los modulos por separado.
3. Que los parametros regulatorios anuales (UMA, tasas, factores) viven en
   una configuracion versionada con fuente oficial, y cumplen sus propias
   identidades legales: UMA anual = UMA mensual x 12 (Ley UMA, Art. 4) y
   la vigencia corre de febrero a enero (la UMA de enero es la del anio
   anterior).

ADVERTENCIA: el RCS de este paquete es una referencia pedagogica. NO es la
formula general de la CUSF ni sustituye el calculo certificado ante la CNSF.

Fuentes: estructura de modulos inspirada en la LISF/CUSF; UMA por INEGI/DOF
via la configuracion anual del paquete (con procedencia consultable).
"""

import warnings
from decimal import Decimal

from suite_actuarial import cargar_config
from suite_actuarial.config.loader import cargar_config_fecha
from suite_actuarial.core.models.regulatorio import (
    ConfiguracionRCSDanos,
    ConfiguracionRCSInversion,
    ConfiguracionRCSVida,
)
from suite_actuarial.regulatorio import AgregadorRCS

warnings.simplefilter("ignore")  # modelos regulatorios marcados experimentales

# ----------------------------------------------------------------------------
# 1. Perfil de la aseguradora (cambie los montos a los de su ejercicio)
# ----------------------------------------------------------------------------
CAPITAL_DISPONIBLE = Decimal("350000000")  # fondos propios admisibles, MXN

config_vida = ConfiguracionRCSVida(
    suma_asegurada_total=Decimal("2500000000"),  # cartera vida en riesgo
    reserva_matematica=Decimal("180000000"),
    edad_promedio_asegurados=38,
    duracion_promedio_polizas=12,
    numero_asegurados=25000,
)
config_danos = ConfiguracionRCSDanos(
    primas_retenidas_12m=Decimal("450000000"),
    reserva_siniestros=Decimal("120000000"),
    coeficiente_variacion=Decimal("0.15"),
    numero_ramos=2,
)
config_inversion = ConfiguracionRCSInversion(
    valor_acciones=Decimal("90000000"),
    valor_bonos_gubernamentales=Decimal("380000000"),
    valor_bonos_corporativos=Decimal("110000000"),
    valor_inmuebles=Decimal("40000000"),
)

agregador = AgregadorRCS(
    config_vida=config_vida,
    config_danos=config_danos,
    config_inversion=config_inversion,
    capital_minimo_pagado=CAPITAL_DISPONIBLE,
)
resultado = agregador.calcular_rcs_completo()

print("=" * 68)
print("Caso 6 - RCS didactico | vida + danios + inversion")
print("=" * 68)
print("RCS por modulo (antes de agregar):")
print(f"  Suscripcion vida:    ${resultado.rcs_suscripcion_vida:>16,.0f}")
print(f"  Suscripcion danios:  ${resultado.rcs_suscripcion_danos:>16,.0f}")
print(f"  Inversion:           ${resultado.rcs_inversion:>16,.0f}")
suma_modulos = (
    resultado.rcs_suscripcion_vida + resultado.rcs_suscripcion_danos + resultado.rcs_inversion
)
print(f"  Suma simple:         ${suma_modulos:>16,.0f}")
print(f"  RCS agregado (corr.):${resultado.rcs_total:>16,.0f}")
print(f"  Beneficio de diversificacion: ${suma_modulos - resultado.rcs_total:>14,.0f}")

cobertura = CAPITAL_DISPONIBLE / resultado.rcs_total
print(f"\nCapital disponible:    ${CAPITAL_DISPONIBLE:>16,.0f}")
print(f"Indice de cobertura (capital / RCS): {cobertura:.2f}x")
print(f"Cubre el requerimiento del modelo: {resultado.cumple_umbral_modelo}")

# ----------------------------------------------------------------------------
# 2. Parametros anuales: UMA con fuente e identidades legales
# ----------------------------------------------------------------------------
cfg_2026 = cargar_config(2026)
uma = cfg_2026.uma
print("\nUMA 2026 (INEGI/DOF, vigente feb-2026 a ene-2027):")
print(f"  diaria ${uma.uma_diaria} | mensual ${uma.uma_mensual} | anual ${uma.uma_anual}")

cfg_enero = cargar_config_fecha("2026-01-15")
print(
    f"En enero de 2026 rige todavia el perfil {cfg_enero.anio} (UMA ${cfg_enero.uma.uma_diaria})."
)

# ----------------------------------------------------------------------------
# 3. Chequeos actuariales
# ----------------------------------------------------------------------------
# a) Solvencia: con $350M de capital el RCS de ~$282M queda cubierto.
assert resultado.cumple_umbral_modelo, "el capital del caso debe cubrir el RCS del modelo"
assert cobertura > 1, "cobertura clasica > 1 cuando el capital excede el RCS"

# b) Diversificacion: agregar con correlaciones nunca excede la suma simple.
assert resultado.rcs_total <= suma_modulos, (
    "la agregacion con correlaciones no puede exceder la suma"
)

# c) Identidad legal de la UMA: anual = mensual x 12 (Ley UMA, Art. 4).
assert uma.uma_anual == uma.uma_mensual * 12, "UMA anual != mensual x 12"
assert uma.uma_mensual == (uma.uma_diaria * Decimal("30.4")).quantize(Decimal("0.01")), (
    "UMA mensual != diaria x 30.4"
)

# d) Vigencia efectiva: en enero rige el perfil del anio anterior.
assert cfg_enero.anio == 2025, "la UMA de enero debe ser la del anio anterior"

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: presentar este RCS como el calculo")
print("certificado CNSF, derivar la UMA anual como diaria x 365, hardcodear")
print("parametros del anio en la logica, y confundir capital con reservas.")
