"""Caso 7 - Reaseguro: cuota parte y capa de exceso de perdida (XL).

El caso
-------
Una aseguradora de danios con cartera expuesta a huracan en la costa del
Golfo estructura su programa de reaseguro 2026 en dos piezas:

1. Un contrato CUOTA PARTE al 30%: cede el 30% de cada prima y de cada
   siniestro, y recibe una comision del 25% sobre la prima cedida (el
   reasegurador le devuelve parte de sus gastos de adquisicion).
2. Una capa CATASTROFICA XL "$80M xs $20M": en un evento catastrofico la
   cedente retiene los primeros $20,000,000 (prioridad) y el reasegurador
   paga el exceso hasta $80,000,000 adicionales (capacidad).

Durante el anio ocurren dos huracanes: uno con perdida de $50M y otro,
extremo, con perdida de $150M.

Que demuestra este caso
-----------------------
1. Cuota parte: retenido + cedido = 100% de primas y siniestros, poliza por
   poliza. Es un reparto proporcional, no una proteccion contra severidad.
2. XL: pago del reasegurador = min(max(0, S - prioridad), capacidad).
   En el evento de $150M la capacidad se AGOTA: el reasegurador paga $80M
   y la cedente absorbe $20M de prioridad MAS $50M de exceso no cubierto.
3. Por que las aseguradoras combinan ambos: la cuota parte libera capital
   proporcionalmente; el XL corta la cola catastrofica.

Fuentes: mecanica estandar de contratos proporcionales y no proporcionales
(practica de mercado; Swiss Re, Introduction to Reinsurance).
"""

import warnings
from datetime import date
from decimal import Decimal

from suite_actuarial.core.models.reaseguro import (
    ExcessOfLossConfig,
    QuotaShareConfig,
    Siniestro,
    TipoContrato,
    TipoSiniestro,
)
from suite_actuarial.reaseguro import ExcessOfLoss, QuotaShare

warnings.simplefilter("ignore")

# ----------------------------------------------------------------------------
# 1. Contrato cuota parte 30% con comision del 25%
# ----------------------------------------------------------------------------
PRIMA_BRUTA_CARTERA = Decimal("120000000")  # primas del ramo en el anio, MXN

quota = QuotaShare(
    QuotaShareConfig(
        tipo_contrato=TipoContrato.QUOTA_SHARE,
        vigencia_inicio=date(2026, 1, 1),
        vigencia_fin=date(2026, 12, 31),
        porcentaje_cesion=Decimal("30"),  # 30% (la config se expresa en %)
        comision_reaseguro=Decimal("25"),  # 25% sobre la prima cedida
    )
)

prima_cedida = quota.calcular_prima_cedida(PRIMA_BRUTA_CARTERA)
prima_retenida = quota.calcular_prima_retenida(PRIMA_BRUTA_CARTERA)
comision = quota.calcular_comision(prima_cedida)

print("=" * 68)
print("Caso 7 - Programa de reaseguro | cuota parte 30% + XL $80M xs $20M")
print("=" * 68)
print(f"Prima bruta de la cartera:  ${PRIMA_BRUTA_CARTERA:>15,.0f}")
print(f"  Prima cedida (30%):       ${prima_cedida:>15,.0f}")
print(f"  Prima retenida (70%):     ${prima_retenida:>15,.0f}")
print(f"  Comision recibida (25%):  ${comision:>15,.0f}")

# ----------------------------------------------------------------------------
# 2. Capa catastrofica XL: $80M en exceso de $20M
# ----------------------------------------------------------------------------
PRIORIDAD = Decimal("20000000")
CAPACIDAD = Decimal("80000000")

huracan_moderado = Siniestro(
    id_siniestro="CAT-2026-01",
    fecha_ocurrencia=date(2026, 3, 10),
    monto_bruto=Decimal("50000000"),
    tipo=TipoSiniestro.EVENTO_CATASTROFICO,
    descripcion="Huracan cat. 2, costa de Veracruz",
)
huracan_extremo = Siniestro(
    id_siniestro="CAT-2026-02",
    fecha_ocurrencia=date(2026, 6, 2),
    monto_bruto=Decimal("150000000"),
    tipo=TipoSiniestro.EVENTO_CATASTROFICO,
    descripcion="Huracan cat. 4, costa de Tamaulipas",
)


def capa_nueva() -> ExcessOfLoss:
    """Capa XL con su capacidad completa (cada evento se evalua por separado)."""
    return ExcessOfLoss(
        ExcessOfLossConfig(
            tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fin=date(2026, 12, 31),
            retencion=PRIORIDAD,
            limite=CAPACIDAD,
            tasa_prima=Decimal("0.05"),
        )
    )


print("\nCapa XL $80M xs $20M, evento por evento:")
print(f"  {'evento':<14} {'perdida':>14} {'reasegurador':>14} {'cedente':>14}")
recuperaciones = {}
for siniestro in (huracan_moderado, huracan_extremo):
    recuperacion = capa_nueva().calcular_recuperacion(siniestro)
    a_cargo_cedente = siniestro.monto_bruto - recuperacion
    recuperaciones[siniestro.id_siniestro] = recuperacion
    print(
        f"  {siniestro.id_siniestro:<14} ${siniestro.monto_bruto:>13,.0f}"
        f" ${recuperacion:>13,.0f} ${a_cargo_cedente:>13,.0f}"
    )

print("\n  En el evento de $150M la capacidad se agota: la cedente absorbe la")
print("  prioridad ($20M) y ademas los $50M que exceden la capa ($100M tope).")

# ----------------------------------------------------------------------------
# 3. Chequeos actuariales
# ----------------------------------------------------------------------------
# a) Cuota parte: cedido + retenido = 100% de la prima.
assert prima_cedida + prima_retenida == PRIMA_BRUTA_CARTERA, "cuota parte no conserva la prima"
assert prima_cedida == PRIMA_BRUTA_CARTERA * Decimal("0.30"), "cesion distinta del 30%"
assert comision == prima_cedida * Decimal("0.25"), "comision distinta del 25% de lo cedido"

# b) XL: pago del reasegurador = min(max(0, S - prioridad), capacidad).
for siniestro in (huracan_moderado, huracan_extremo):
    esperado = min(max(Decimal("0"), siniestro.monto_bruto - PRIORIDAD), CAPACIDAD)
    assert recuperaciones[siniestro.id_siniestro] == esperado, (
        f"formula XL incorrecta en {siniestro.id_siniestro}"
    )

# c) Valores concretos del caso: 50M -> 30M; 150M -> 80M (capacidad agotada).
assert recuperaciones["CAT-2026-01"] == Decimal("30000000")
assert recuperaciones["CAT-2026-02"] == Decimal("80000000")

# d) Monotonia: subir la prioridad reduce lo que paga el reasegurador.
capa_prioridad_alta = ExcessOfLoss(
    ExcessOfLossConfig(
        tipo_contrato=TipoContrato.EXCESS_OF_LOSS,
        vigencia_inicio=date(2026, 1, 1),
        vigencia_fin=date(2026, 12, 31),
        retencion=Decimal("30000000"),
        limite=CAPACIDAD,
        tasa_prima=Decimal("0.05"),
    )
)
assert capa_prioridad_alta.calcular_recuperacion(huracan_moderado) < recuperaciones["CAT-2026-01"]

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: creer que el XL cubre todo el")
print("exceso sin tope (ignora la capacidad), confundir la prioridad de una")
print("capa con la retencion proporcional de un cuota parte, y olvidar la")
print("comision de reaseguro al evaluar el costo neto del programa.")
