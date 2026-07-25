"""Laboratorio 01: construcción de un dotal educativo 20/10.

Pregunta de producto
--------------------
¿Cómo financiar un beneficio de MXN 1,000,000 que se pague si el asegurado
fallece durante 20 años o si sobrevive al vencimiento, concentrando las primas
en los primeros 10 años?

La tabla EMSSA-09 incluida es ilustrativa. Este caso demuestra mecánica,
trazabilidad e identidades; no constituye una cotización comercial.
"""

from decimal import Decimal

from suite_actuarial import Asegurado, ConfiguracionProducto, TablaMortalidad
from suite_actuarial.core.models.common import Sexo
from suite_actuarial.vida import VidaDotal

tabla = TablaMortalidad.cargar_emssa09()
config = ConfiguracionProducto(
    nombre_producto="Dotal educativo 20/10",
    plazo_years=20,
    tasa_interes_tecnico=Decimal("0.055"),
    recargo_gastos_admin=Decimal("0.05"),
    recargo_gastos_adq=Decimal("0.10"),
    recargo_utilidad=Decimal("0.03"),
)
asegurado = Asegurado(
    edad=35,
    sexo=Sexo.HOMBRE,
    suma_asegurada=Decimal("1000000"),
)
producto = VidaDotal(config, tabla, plazo_pago=10)
analisis = producto.analizar_producto(asegurado)

print("Dotal educativo 20/10")
print(f"VP beneficio por muerte:       ${analisis.vp_beneficio_muerte:,.2f}")
print(f"VP beneficio por supervivencia:${analisis.vp_beneficio_supervivencia:,.2f}")
print(f"Prima neta anual:              ${analisis.prima_neta_anual_equivalente:,.2f}")
print(f"Prima total anual:             ${analisis.resultado_prima.prima_total:,.2f}")

for punto in analisis.reservas:
    if punto.anio in {0, 5, 10, 15, 20}:
        print(f"Reserva año {punto.anio:>2}: ${punto.reserva:,.2f}")

# Cada verificación contrasta el motor de valuación contra una ruta de cálculo
# distinta: las funciones de conmutación (Dx/Nx/Mx) para la descomposición del
# beneficio, y la recursión de Fackler -- retrospectiva -- para la trayectoria de
# la reserva, que aquí se calcula de forma prospectiva. Los campos `diferencia_*`
# muestran el margen, no solo un booleano.
checks = analisis.verificaciones
assert checks.descomposicion_beneficios
assert checks.principio_equivalencia
assert checks.reserva_inicial_cero
assert checks.reserva_final_igual_beneficio
assert checks.recursion_fackler

print("\nVerificaciones (contra oraculos independientes):")
print("  Muerte + supervivencia = SA*(A1_x:n + nEx) por conmutacion")
print(f"    diferencia relativa:        {checks.diferencia_descomposicion:.2e}")
print("  Prima del motor * anualidad = VP beneficios")
print(f"    diferencia absoluta:        ${checks.diferencia_equivalencia:,.6f}")
print("  Recursion de Fackler entre reservas consecutivas")
print(f"    diferencia relativa maxima: {checks.diferencia_recursion:.2e}")
print(f"  Reserva en t=0:               ${analisis.reservas[0].reserva:,.2f}")
print(f"  Reserva en t=20:              ${analisis.reservas[-1].reserva:,.2f}")
print("\nTodas las verificaciones actuariales se cumplen.")
