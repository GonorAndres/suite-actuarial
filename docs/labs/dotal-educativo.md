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

La implementación comprueba:

- descomposición del valor presente de beneficios;
- principio de equivalencia dentro de tolerancia de redondeo;
- reserva inicial igual a cero sobre la base neta;
- reserva final igual al beneficio de supervivencia pagadero.

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
