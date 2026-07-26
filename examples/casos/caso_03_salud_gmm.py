"""Caso 3 - Salud: gastos medicos mayores con deducible, coaseguro y trend.

El caso
-------
Laura, 45 anios, contrata un plan de gastos medicos mayores (GMM) con suma
asegurada de $5,000,000 MXN, deducible de $40,000, coaseguro del 10% con tope
de $50,000, hospitales de nivel medio en zona urbana. Un anio despues sufre
una apendicectomia complicada con gasto hospitalario de $180,000 MXN y quiere
saber cuanto pagara de su bolsillo.

Que demuestra este caso
-----------------------
1. Como se reparte un siniestro de GMM entre asegurado y aseguradora:
   el asegurado paga deducible + coaseguro sobre el excedente; la
   aseguradora paga el resto (nunca mas que la suma asegurada).
2. La curva de morbilidad: la prima crece con la edad aunque la persona
   este sana, porque la probabilidad y el costo de reclamar suben.
3. El trend medico: la inflacion de costos hospitalarios en Mexico corre
   varios puntos ARRIBA del INPC; usar la inflacion general subestima la
   prima de renovacion.

Fuentes: tasas base ilustrativas del paquete (ver DISCLAIMER de la clase
GMM); practica de mercado mexicana para deducible ($20,000-$60,000) y
coaseguro (10% con tope).
"""

from decimal import Decimal

from suite_actuarial.salud import GMM, NivelHospitalario, ZonaGeografica

# ----------------------------------------------------------------------------
# 1. El plan de Laura
# ----------------------------------------------------------------------------
plan = GMM(
    edad=45,
    sexo="F",
    suma_asegurada=Decimal("5000000"),
    deducible=Decimal("40000"),
    coaseguro_pct=Decimal("0.10"),
    tope_coaseguro=Decimal("50000"),
    zona=ZonaGeografica.URBANO,
    nivel=NivelHospitalario.MEDIO,
)

prima = plan.calcular_prima_ajustada()

print("=" * 68)
print("Caso 3 - GMM | mujer 45 anios | SA $5,000,000 | ded $40,000 | coas 10%")
print("=" * 68)
print(f"Prima anual ajustada: ${prima:>12,.2f} MXN")
print("Desglose:")
for concepto, valor in plan.desglose_prima().items():
    print(f"  {concepto:<28} {valor}")

# ----------------------------------------------------------------------------
# 2. El siniestro de $180,000: quien paga que
# ----------------------------------------------------------------------------
GASTO = Decimal("180000")
reparto = plan.simular_gasto_medico(GASTO)

print(f"\nSiniestro hospitalario de ${GASTO:,.2f}:")
for concepto, monto in reparto.items():
    print(f"  {concepto:<28} ${Decimal(str(monto)):>12,.2f}")


# ----------------------------------------------------------------------------
# 3. Curva de morbilidad: misma cobertura a 30, 45 y 60 anios
# ----------------------------------------------------------------------------
def prima_a_edad(edad: int) -> Decimal:
    return GMM(
        edad=edad,
        sexo="F",
        suma_asegurada=Decimal("5000000"),
        deducible=Decimal("40000"),
        coaseguro_pct=Decimal("0.10"),
        tope_coaseguro=Decimal("50000"),
        zona=ZonaGeografica.URBANO,
        nivel=NivelHospitalario.MEDIO,
    ).calcular_prima_ajustada()


primas_por_edad = {edad: prima_a_edad(edad) for edad in (30, 45, 60)}
print("\nMisma cobertura, distinta edad (curva de morbilidad):")
for edad, p in primas_por_edad.items():
    print(f"  {edad} anios: ${p:>12,.2f}")

# ----------------------------------------------------------------------------
# 4. Trend medico: proyeccion de la prima de renovacion a 3 anios
# ----------------------------------------------------------------------------
TREND_MEDICO = Decimal("0.10")  # ~10% anual, tipico en Mexico (INPC + 4-6 pts)
INPC = Decimal("0.045")  # inflacion general de referencia

print("\nPrima proyectada con trend medico 10% vs INPC 4.5%:")
for anio in (1, 2, 3):
    con_trend = prima * (1 + TREND_MEDICO) ** anio
    con_inpc = prima * (1 + INPC) ** anio
    print(f"  renovacion +{anio}: trend ${con_trend:>12,.2f} | INPC ${con_inpc:>12,.2f}")

# ----------------------------------------------------------------------------
# 5. Chequeos actuariales
# ----------------------------------------------------------------------------
# a) Reparto del siniestro: deducible + coaseguro sobre el excedente.
#    Bolsillo esperado = 40,000 + 10% x (180,000 - 40,000) = $54,000
excedente = GASTO - Decimal("40000")
coaseguro_esperado = min(excedente * Decimal("0.10"), Decimal("50000"))
bolsillo_esperado = Decimal("40000") + coaseguro_esperado
pago_asegurado = Decimal(str(reparto["pago_total_asegurado"]))
pago_aseguradora = Decimal(str(reparto["pago_aseguradora"]))
assert pago_asegurado == bolsillo_esperado, "Reparto deducible/coaseguro incorrecto"

# b) Conservacion: asegurado + aseguradora = gasto total.
assert pago_asegurado + pago_aseguradora == GASTO, "El reparto debe sumar el gasto total"

# c) Curva de morbilidad: la prima crece con la edad.
assert primas_por_edad[30] < primas_por_edad[45] < primas_por_edad[60], (
    "La prima de GMM debe crecer con la edad"
)

# d) El trend medico supera al INPC: usar INPC subestima la renovacion.
assert TREND_MEDICO > INPC, "El trend medico en Mexico corre arriba del INPC"

print("\nTodos los chequeos actuariales se cumplen.")
print("Errores tipicos que este caso evita: aplicar el coaseguro sobre el")
print("gasto bruto en lugar del excedente del deducible, proyectar renovaciones")
print("con INPC, y confundir la suma asegurada (tope) con el gasto esperado.")
