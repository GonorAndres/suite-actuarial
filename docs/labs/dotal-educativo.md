# Laboratorio 01: dotal educativo 20/10

## Propósito

Construir un producto que financie un capital educativo dentro de 20 años y mantenga la
protección si el asegurado fallece antes. Las primas se concentran en los primeros 10 años.
Es clásico, pero no trivial: separa dos beneficios contingentes y crea una obligación que
continúa después de terminar el pago de primas.

## Promesa contractual

- Si el asegurado fallece durante los 20 años, se paga la suma asegurada.
- Si sobrevive al final del año 20, se paga la misma suma asegurada.
- Se pagan primas niveladas anticipadas como máximo durante 10 años y mientras viva.

Los dos beneficios son mutuamente excluyentes para una póliza; su valor presente actuarial
sí puede descomponerse y sumarse.

## Supuestos iniciales

| Supuesto | Valor de demostración |
|---|---:|
| Edad | 35 años |
| Sexo de tabla | Hombre |
| Suma asegurada | MXN 1,000,000 |
| Cobertura | 20 años |
| Pago de primas | 10 años |
| Interés técnico | 5.5% anual efectivo |
| Mortalidad | EMSSA-09 incluida en el repositorio |

La tabla incluida debe tratarse según su metadata y las limitaciones de
[VALIDATION.md](../VALIDATION.md). No constituye por sí sola una base de tarificación
vigente o suficiente.

## Método

El valor presente del beneficio dotal se separa en fallecimiento y supervivencia:

```text
VP(beneficios) = VP(fallecimiento durante n años) + VP(supervivencia al año n)
```

La prima neta anual equivalente sigue el principio de equivalencia:

```text
prima neta × anualidad de primas de m años = VP(beneficios)
```

Aquí `n = 20` y `m = 10`. Como el beneficio se financia en menos años que la cobertura, la
prima anual 20/10 debe ser mayor que la prima equivalente con pagos durante 20 años, bajo
los mismos supuestos.

La reserva prospectiva en cada aniversario es el valor presente de beneficios futuros menos
el valor presente de primas futuras. Una vez terminado el plazo de pago, ya no hay primas
futuras que compensen la obligación.

## Qué observar

- cuánto valor aporta el beneficio por muerte frente al de supervivencia;
- cómo responde la prima a edad, interés, suma y plazo de pago;
- cómo cambia la pendiente de la reserva después del año 10;
- por qué la reserva final converge a la suma asegurada;
- qué resultado es contractual y cuál depende de un supuesto técnico.

## Verificaciones

Una verificación sólo sirve si puede fallar. Cada una de las siguientes contrasta el
motor de valuación contra una **ruta de cálculo independiente**, no contra sí mismo:

- **Descomposición del valor presente de beneficios.** Se contrasta contra
  `SA · (A¹_{x:n̄} + ₙE_x)` calculado con funciones de conmutación
  (`(M_x − M_{x+n} + D_{x+n}) / D_x`). Las columnas de conmutación acumulan desde una
  raíz de `lₓ`; el motor de pricing suma `v^{t+1} · ₜp_x · q_{x+t}` año por año. Son
  dos implementaciones distintas del mismo valor actuarial. Si se omite la pierna de
  supervivencia, la verificación falla.
- **Principio de equivalencia.** Se contrasta la prima que devuelve `calcular_prima`
  —la salida real del motor— contra el valor presente de los beneficios. Una prima
  desviada 1% rompe la verificación.
- **Reserva inicial igual a cero** y **reserva final igual al beneficio**. Ambas
  provienen de la fórmula prospectiva, no de constantes: en `t=0` la reserva vale cero
  por el principio de equivalencia, y en `t=n` el dotal a plazo cero vale la suma
  asegurada sin primas pendientes.
- **Recursión de Fackler** (Bowers et al., cap. 7):
  `(ₜV + P)(1+i) = q_{x+t}·SA + p_{x+t}·ₜ₊₁V`. Es una relación *retrospectiva* entre
  reservas consecutivas, mientras la reserva se calcula de forma *prospectiva*, así que
  recorre la trayectoria completa. Es la única de las cuatro que detecta una reserva
  intermedia desviada.

Los campos `diferencia_descomposicion`, `diferencia_equivalencia` y
`diferencia_recursion` reportan el margen contra cada identidad, para juzgar la
holgura en vez de confiar en un booleano.

> Nota histórica: hasta julio de 2026 estas cuatro comprobaciones eran autocumplidas
> (hallazgo A9 de [`docs/AUDIT.md`](../AUDIT.md)). `vp_total` se *definía* como su
> propia descomposición, el principio de equivalencia comparaba un valor consigo mismo,
> y las dos reservas frontera leían constantes escritas dentro de `calcular_reserva`.
> Ninguna podía fallar.

Ejecuta el caso reproducible:

```bash
python examples/labs/lab_01_dotal_educativo.py
```

O abre `/lab` en la aplicación web. El botón de código muestra la representación Python sólo
cuando sea útil; el recorrido actuarial funciona sin conocer la arquitectura técnica.

## Extensiones sugeridas

- comparar pago 10, 15 y 20;
- introducir gastos y distinguir prima neta de tarifa;
- probar mortalidad alternativa y sensibilidad de interés;
- modelar rescate, lapsos o participación de utilidades;
- convertir el caso individual en una cartera y estudiar suficiencia.
