# Cumplimiento Regulatorio -- suite_actuarial

Mapeo de modulos del codigo fuente a normatividad mexicana aplicable.

## CNSF -- Comision Nacional de Seguros y Fianzas

### Circular Unica de Seguros y Fianzas (CUSF)

| Titulo/Capitulo | Tema | Modulo en codigo | Estado |
|----------------|------|-----------------|--------|
| Titulo 22, Cap. 1 | Reservas tecnicas - Reserva Matematica | `regulatorio/reservas_tecnicas/reserva_matematica.py` | Implementado |
| Titulo 22, Cap. 2 | Reservas tecnicas - Riesgos en Curso | `regulatorio/reservas_tecnicas/reserva_riesgos_curso.py` | Implementado |
| Titulo 22, Cap. 3 | Suficiencia de reservas | `regulatorio/reservas_tecnicas/validador_suficiencia.py` | Implementado |
| Titulo 5, Cap. 6 | RCS Vida (suscripcion) | `regulatorio/rcs_vida.py` | Implementado |
| Titulo 5, Cap. 7 | RCS Danos (prima y reserva) | `regulatorio/rcs_danos.py` | Implementado |
| Titulo 5, Cap. 8 | RCS Inversion (mercado, credito) | `regulatorio/rcs_inversion.py` | Implementado |
| Titulo 5, Cap. 9 | Agregacion de RCS | `regulatorio/agregador_rcs.py` | Implementado |

### Circular S-11.4 (Reservas Tecnicas)

- Reserva Matematica (metodo prospectivo) -- Implementado
- Reserva de Riesgos en Curso (pro-rata temporis) -- Implementado
- Margen de seguridad (5%) -- Implementado via config
- Tasa de interes tecnico maxima (5.5%) -- Implementado via config

## SAT -- Servicio de Administracion Tributaria

### Ley del Impuesto Sobre la Renta (LISR)

| Articulo | Tema | Modulo | Estado |
|----------|------|--------|--------|
| Art. 93, fracc. IV | Gastos medicos exentos | `validaciones_sat/validador_siniestros.py` | Implementado |
| Art. 93, fracc. XIII | Indemnizacion por muerte exenta | `validaciones_sat/validador_siniestros.py` | Implementado |
| Art. 93, fracc. XIV | Invalidez exenta | `validaciones_sat/validador_siniestros.py` | Implementado |
| Art. 93, fracc. XV | Danos patrimoniales exentos | `validaciones_sat/validador_siniestros.py` | Implementado |
| Art. 142 | Rentas vitalicias parcialmente gravables | `validaciones_sat/validador_siniestros.py` | Implementado (simplificado) |
| Art. 151, fracc. V | Deducibilidad de primas PF | `validaciones_sat/validador_primas.py` | Implementado |
| Art. 158 | Retiros de ahorro gravables | `validaciones_sat/validador_siniestros.py` | Implementado |
| Art. 25 | Deducibilidad de primas PM | `validaciones_sat/validador_primas.py` | Implementado |

### IMSS -- Instituto Mexicano del Seguro Social

| Ley/Articulo | Tema | Modulo | Estado |
|-------------|------|--------|--------|
| LSS 1973, Art. 167 | Porcentajes de pension por semanas | `pensiones/tablas_imss.py` | Implementado (500-2060 semanas) |
| LSS 1973, Art. 171 | Factores por edad (60-65) | `pensiones/tablas_imss.py` | Implementado |
| LSS 1997, Art. 168 | Cuota social | `pensiones/tablas_imss.py` | Implementado |
| LSS 1997, Art. 170 | Pension garantizada | `pensiones/tablas_imss.py` | Implementado (2024-2026) |
| Reforma 2020 | Semanas minimas transicionales | `pensiones/tablas_imss.py` | Implementado (775-1000) |

## Que NO esta implementado

- CUSF Titulo 22, Cap. 4-8: Reservas para seguros de danos (IBNR regulatorio vs. best estimate)
- CUSF Titulo 5, Cap. 10-12: RCS operativo y catastrofico
- SIPRES: Sistema de Presentacion de Informacion de Reaseguro
- Reportes trimestrales CNSF (formato oficial XML)
- CONSAR: Regimen de inversion de SIEFORES
- Circular S-11.5: Concentracion de riesgos (implementacion parcial)
- Art. 142 LISR completo: Tabla actuarial para gravabilidad de rentas (se usa simplificacion 50/50)
