# Visión del proyecto

## La idea

`suite_actuarial` es una plataforma abierta para construir, probar y comprender modelos
actuariales. Cada modelo conecta una pregunta de producto con beneficios, supuestos,
métodos, resultados, pruebas y código reproducible.

Nace en el mercado mexicano, donde la terminología, las instituciones y varias referencias
del repositorio son específicas. Su ambición es más amplia: los métodos clásicos, el hábito
de declarar supuestos y las identidades de validación pueden ser útiles para estudiantes,
actuarios, investigadores y equipos de innovación en otros mercados.

## Para quién

- estudiantes que quieren ir de la fórmula a un producto completo;
- actuarios en sus primeros años que necesitan experimentar con supuestos;
- docentes e investigadores que requieren benchmarks reproducibles;
- equipos de innovación que necesitan una base visible antes de industrializar una idea;
- desarrolladores que colaboran con actuarios y necesitan contratos claros.

Su alcance es educativo y experimental. Los usos profesionales requieren datos validados,
gobierno interno, métodos aprobados y juicio actuarial responsable.

## Qué hace que un modelo pueda compartirse

Todo modelo publicado en la plataforma debe permitir responder seis preguntas:

1. ¿Qué problema intenta resolver?
2. ¿Qué promete pagar y bajo qué eventos?
3. ¿Qué se asumió y de dónde viene?
4. ¿Cómo transforma el método esos supuestos?
5. ¿Qué significa el resultado y cómo cambia?
6. ¿Qué identidad, contraste o límite permite confiar en él?

La interfaz presenta primero el razonamiento actuarial. El método permanece visible y el código
queda disponible como una segunda capa para reproducir y extender el análisis.

## Arquitectura editorial

- **Inicio:** propósito de la plataforma, método común y ejemplo guiado.
- **Ejemplos guiados:** recorridos de propósito a validación.
- **Biblioteca:** modelos agrupados por preguntas actuariales.
- **Evidencia:** fuentes, vigencia, pruebas y limitaciones.
- **Referencia técnica:** Python, contratos de datos e integración.
- **Comunidad:** propuestas, discusión y extensiones, construidas gradualmente sobre una base
  editorial estable.

## Principios

- La transparencia reúne código, supuestos, fuentes y alcance.
- Las pruebas documentan el comportamiento implementado y el nivel de validación alcanzado.
- México aporta el contexto de origen y cada modelo identifica qué elementos son generalizables.
- La precisión del lenguaje importa tanto como la precisión numérica.
- Cada interfaz debe acercar el modelo al razonamiento actuarial.
