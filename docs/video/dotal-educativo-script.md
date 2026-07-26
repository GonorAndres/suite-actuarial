# Guion de demo: construyendo un dotal educativo 20/10

Duración objetivo: 8–10 minutos. Pantalla principal: `/lab`. El video debe mostrar decisiones,
no una visita exhaustiva a menús.

## 0:00 — La pregunta

“Quiero financiar un capital educativo dentro de 20 años, pero también proteger ese objetivo
si la persona que lo financia fallece antes. Vamos a construir el producto y a revisar si los
números cuentan la misma historia que el contrato.”

Mostrar el título del laboratorio. No mencionar API ni arquitectura.

## 0:45 — Beneficios

Recorrer los dos eventos: fallecimiento dentro del plazo y supervivencia al vencimiento.
Subrayar que sólo uno se paga, pero ambos contribuyen al valor presente esperado.

## 1:45 — Supuestos

Usar edad 35, suma MXN 1,000,000, cobertura 20, primas 10 e interés 5.5%. Explicar qué es una
decisión de diseño y qué viene de una base técnica. Mostrar el aviso de mortalidad ilustrativa.

## 3:00 — Método

Presentar la descomposición `muerte + supervivencia` y el principio de equivalencia en lenguaje
natural. Abrir el código opcional brevemente para demostrar reproducibilidad, no para enseñar
la interfaz técnica.

## 4:15 — Prima y sensibilidad

Mostrar la prima. Cambiar primero el plazo de pago de 10 a 20 y volver a 10. Después cambiar
la tasa. Narrar la dirección esperada antes de ver el resultado.

## 5:45 — Reserva

Recorrer la gráfica del año 0 al 20. Señalar el año 10, cuando terminan las primas, y el valor
final. Evitar describir la gráfica sólo visualmente: conectar su forma con la obligación futura.

## 7:00 — Verificaciones

Mostrar las cuatro verificaciones. Explicar que pasar pruebas no certifica los supuestos; indica
que la implementación respeta las identidades declaradas.

## 8:00 — Invitación

“Este laboratorio es una base, no un producto terminado. Puedes cambiar supuestos, ejecutar el
script, proponer otra fuente o extender los flujos. La conversación actuarial queda junto al
código, en abierto.”

Cerrar con el repositorio y la ruta a `docs/labs/dotal-educativo.md`.
