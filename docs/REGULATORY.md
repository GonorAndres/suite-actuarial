# Referencia regulatoria y modelos experimentales -- suite_actuarial

Este documento describe referencias de modelado para aprendizaje, análisis y
comparación de supuestos. No certifica cumplimiento CNSF, SAT, CONSAR o IMSS.
Una función etiquetada como "Implementado" significa que existe código y pruebas
para el alcance descrito; no significa que replique el método regulatorio completo
ni que esté aprobada para uso institucional.

## Cómo leer el estado de un modelo

- **Implementado -- referencia:** hay una implementación ejecutable para el
  alcance documentado, con pruebas de comportamiento o identidades relevantes.
- **Experimental/simplificado:** usa datos ilustrativos, factores pedagógicos,
  supuestos incompletos o una interpretación que requiere revisión independiente.
- **Parcial/no implementado:** el alcance regulatorio completo todavía no está
  cubierto por este repositorio.

Antes de usar un resultado en un análisis profesional, revise la fuente, la fecha
de vigencia, las unidades, los supuestos y las advertencias del cálculo.

Mapeo de modulos del codigo fuente a normatividad mexicana aplicable.

## CNSF -- Comision Nacional de Seguros y Fianzas

### Circular Unica de Seguros y Fianzas (CUSF)

| Titulo/Capitulo | Tema | Modulo en codigo | Estado |
|----------------|------|-----------------|--------|
| Titulo 22, Cap. 1 | Reservas tecnicas - Reserva Matematica | `regulatorio/reservas_tecnicas/reserva_matematica.py` | Implementado -- referencia; validar contra el método institucional |
| Titulo 22, Cap. 2 | Reservas tecnicas - Riesgos en Curso | `regulatorio/reservas_tecnicas/reserva_riesgos_curso.py` | Implementado -- referencia; alcance simplificado |
| Titulo 22, Cap. 3 | Suficiencia de reservas | `regulatorio/reservas_tecnicas/validador_suficiencia.py` | Implementado -- referencia; no certifica suficiencia regulatoria |
| Titulo 5, Cap. 6 | RCS Vida (suscripcion) | `regulatorio/rcs_vida.py` | Experimental/simplificado |
| Titulo 5, Cap. 7 | RCS Danos (prima y reserva) | `regulatorio/rcs_danos.py` | Experimental/simplificado |
| Titulo 5, Cap. 8 | RCS Inversion (mercado, credito) | `regulatorio/rcs_inversion.py` | Experimental/simplificado |
| Titulo 5, Cap. 9 | Agregacion de RCS | `regulatorio/agregador_rcs.py` | Implementado -- referencia; factores sujetos a revisión |

### Circular S-11.4 (Reservas Tecnicas)

- Reserva Matematica (metodo prospectivo) -- referencia implementada; requiere validación institucional
- Reserva de Riesgos en Curso (pro-rata temporis) -- referencia implementada; alcance simplificado
- Margen de seguridad (5%) -- parámetro de referencia en config, no una determinación universal
- Tasa de interes tecnico maxima (5.5%) -- parámetro de referencia en config, sujeto a producto y vigencia

## SAT -- Servicio de Administracion Tributaria

### Ley del Impuesto Sobre la Renta (LISR)

| Articulo | Tema | Modulo | Estado |
|----------|------|--------|--------|
| Art. 93, fracc. IV | Gastos medicos exentos | `validaciones_sat/validador_siniestros.py` | Implementado -- referencia; revisar caso concreto |
| Art. 93, fracc. XIII | Indemnizacion por muerte exenta | `validaciones_sat/validador_siniestros.py` | Implementado -- referencia; revisar caso concreto |
| Art. 93, fracc. XIV | Invalidez exenta | `validaciones_sat/validador_siniestros.py` | Implementado -- referencia; revisar caso concreto |
| Art. 93, fracc. XV | Danos patrimoniales exentos | `validaciones_sat/validador_siniestros.py` | Implementado -- referencia; revisar caso concreto |
| Art. 142 | Rentas vitalicias parcialmente gravables | `validaciones_sat/validador_siniestros.py` | Experimental/simplificado |
| Art. 151, fracc. V | Deducibilidad de primas PF | `validaciones_sat/validador_primas.py` | Implementado -- referencia; no es asesoría fiscal |
| Art. 158 | Retiros de ahorro gravables | `validaciones_sat/validador_siniestros.py` | Implementado -- referencia; no es asesoría fiscal |
| Art. 25 | Deducibilidad de primas PM | `validaciones_sat/validador_primas.py` | Implementado -- referencia; no es asesoría fiscal |

### IMSS -- Instituto Mexicano del Seguro Social

| Ley/Articulo | Tema | Modulo | Estado |
|-------------|------|--------|--------|
| LSS 1973, Art. 167 | Porcentajes de pension por semanas | `pensiones/tablas_imss.py` | Implementado -- referencia (500-2060 semanas) |
| LSS 1973, Art. 171 | Factores por edad (60-65) | `pensiones/tablas_imss.py` | Implementado -- referencia |
| LSS 1997, Art. 168 | Cuota social | `pensiones/tablas_imss.py` | Implementado -- referencia |
| LSS 1997, Art. 170 | Pension garantizada | `pensiones/tablas_imss.py` | Implementado -- referencia (2024-2026) |
| Reforma 2020 | Semanas minimas transicionales | `pensiones/tablas_imss.py` | Implementado -- referencia (775-1000) |

## Que NO esta implementado

- CUSF Titulo 22, Cap. 4-8: Reservas para seguros de danos (IBNR regulatorio vs. best estimate)
- CUSF Titulo 5, Cap. 10-12: RCS operativo y catastrofico
- SIPRES: Sistema de Presentacion de Informacion de Reaseguro
- Reportes trimestrales CNSF (formato oficial XML)
- CONSAR: Regimen de inversion de SIEFORES
- Circular S-11.5: Concentracion de riesgos (implementacion parcial)
- Art. 142 LISR completo: Tabla actuarial para gravabilidad de rentas (se usa simplificacion 50/50)
