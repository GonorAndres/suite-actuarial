# Casos de uso por dominio

Siete casos trabajados, uno por dominio actuarial, pensados para que un
actuario, un estudiante o un desarrollador entienda QUE hace la suite y COMO
usarla sin tener que leer la API primero. Cada caso:

- cuenta una situacion realista del mercado mexicano (personas, montos y
  parametros plausibles 2025-2026);
- muestra la secuencia minima de codigo para resolverla con el paquete;
- verifica identidades actuariales duras con `assert` (si una falla, el
  script truena: los numeros no son decorativos, son comprobables);
- cita la fuente de sus tablas y parametros; y
- termina con los errores tipicos que ese calculo suele provocar.

La intencion es que sirvan como base: copie el caso, cambie las variables de
la seccion "supuestos" y tendra un calculo con metodos verificados. No son
notas tecnicas registrables ante la CNSF; son una referencia pedagogica y de
desarrollo (vea `docs/REGULATORY.md` para los alcances).

## Los casos

| # | Archivo | Dominio | Que demuestra |
|---|---------|---------|----------------|
| 1 | `caso_01_vida_temporal.py` | Vida | Principio de equivalencia, prima neta vs tarifa, perfil de la reserva de una temporal |
| 2 | `caso_02_danos_auto.py` | Danios | Prima pura = frecuencia x severidad, efecto del deducible, VaR de la perdida agregada |
| 3 | `caso_03_salud_gmm.py` | Salud | Reparto deducible/coaseguro de un siniestro GMM, curva de morbilidad, trend medico vs INPC |
| 4 | `caso_04_pensiones_imss.py` | Pensiones | Ley 73 vs Ley 97, tope de 25 UMA, renta vitalicia que agota el saldo AFORE |
| 5 | `caso_05_reservas_chain_ladder.py` | Reservas | Chain Ladder sobre un triangulo de pagados, ultimate >= pagado, incertidumbre de Mack |
| 6 | `caso_06_regulatorio_rcs.py` | Regulatorio | RCS didactico por modulos, beneficio de diversificacion, UMA anual = mensual x 12 |
| 7 | `caso_07_reaseguro.py` | Reaseguro | Cuota parte (retenido + cedido = 100%) y capa XL con agotamiento de capacidad |

## Como ejecutarlos

Desde la raiz del repositorio, con el paquete instalado (`pip install -e ".[dev]"`):

```bash
python examples/casos/caso_01_vida_temporal.py
```

Cada script es autocontenido y termina imprimiendo
`Todos los chequeos actuariales se cumplen.` si las identidades se
verificaron. Los cuadernos de `examples/*.ipynb` cubren los mismos dominios
con graficas y mas detalle.

## Identidades que cada caso hace cumplir

| Dominio | Identidad |
|---------|-----------|
| Vida | `P x a''(x:n) = SA x A(x:n)`; reserva t=0 y t=n de una temporal ~ 0 |
| Danios | `E[S] = E[N] x E[X]`; mas deducible => menos prima |
| Salud | bolsillo = deducible + coaseguro x excedente; asegurado + aseguradora = gasto |
| Pensiones | prima unica = pension anual x a''(x); UMA != salario minimo |
| Reservas | ultimate >= pagado; reserva = suma(ultimate - pagado); factores decrecen a 1 |
| Regulatorio | RCS agregado <= suma de modulos; UMA anual = mensual x 12; enero usa el perfil anterior |
| Reaseguro | retenido + cedido = 100%; pago XL = min(max(0, S - prioridad), capacidad) |
