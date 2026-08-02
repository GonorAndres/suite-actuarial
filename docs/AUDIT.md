# Auditoría actuarial — `suite_actuarial`

Fecha de la auditoría: 2026-07-22. Remediación completa: 2026-07-25. Alcance:
revisión actuarial de corrección (no de estilo) del paquete Python, con verificación
numérica a mano por dominio.

**Estado: las seis fases de la [orden de remediación](#orden-de-remediación) están
cerradas.** El documento se conserva íntegro — hallazgos, evidencia original y
registro de cierre — como constancia de la revisión. Los enunciados de la sección
[Clase A](#clase-a--defectos-reales) describen el código **antes** de la corrección;
lo que quedó vigente después está en el [registro de cierre](#registro-de-cierre) y en
el [inventario Clase B](#inventario-clase-b-fase-5).

Objetivo de calidad: llevar el repositorio al nivel interno **Platino** definido
en este documento. Platino significa que un modelo publicado es trazable,
reproducible y está protegido contra los errores actuariales conocidos; **no**
significa que esté aprobado por la CNSF, que sustituya una nota técnica ni que sus
datos ilustrativos sean aptos para uso profesional.

Método: lectura directa del núcleo (mortalidad, interés, valuación) y del motor
regulatorio, más auditoría paralela por dominio (vida, reservas, pensiones/salud,
daños/reaseguro) con contraste de fórmulas a mano contra los datos incluidos.
Estado de la suite al momento de auditar: 989 pruebas en verde, cobertura 89%.

## Cómo leer esta auditoría

Los hallazgos se separan en dos clases:

- **Clase A — defectos reales.** Producen un número incorrecto o rechazan una
  entrada válida, con independencia de la calidad de los datos. Deben corregirse
  para sostener credibilidad, incluso a nivel educativo.
- **Clase B — simplificaciones declaradas.** Son aceptables dado el marco de
  honestidad del proyecto (avisos `ExperimentalModelWarning`, datos marcados como
  ilustrativos), pero son techos para el uso profesional.

Severidad: **Crítica** (resultado público equivocado o método inválido presentado
como válido), **Mayor** (número sistemáticamente sesgado o entrada válida
bloqueada), **Menor** (inconsistencia acotada o de convención).

## Estándar Platino y regla de cierre

Un hallazgo no se considera cerrado porque la suite esté en verde. Se cierra sólo
cuando el cambio cumple todos los criterios aplicables:

1. **Corrección demostrable.** Existe una prueba que habría fallado con la
   implementación defectuosa. La expectativa procede de una identidad actuarial,
   un cálculo manual reproducible, un caso límite o una fuente identificada; no de
   repetir la fórmula bajo prueba.
2. **Contrato coherente.** La misma cantidad conserva definición, unidades,
   orientación y redondeo en paquete, API, reportes, ejemplos y pruebas. Si el
   contrato público cambia, se documenta la migración.
3. **Supuestos honestos.** Todo parámetro ilustrativo, simplificación o dato sin
   vigencia verificable se muestra como tal en el resultado y en su documentación.
   No se etiqueta como método regulatorio ni de mercado sin evidencia.
4. **Trazabilidad.** El cierre nombra archivos modificados, prueba(s), fuente o
   justificación, y el límite que sigue vigente. Esta auditoría se actualiza con
   fecha y enlace al cambio.
5. **No regresión.** Pasan las verificaciones relevantes del repositorio: `pytest`,
   `ruff check src/ tests/`, `ruff format --check src/ tests/` y `mypy src/ tests/`.
   Si cambia una interfaz, también pasan sus pruebas de contrato y las
   verificaciones del frontend.

Un modelo puede llamarse **Platino** sólo cuando no tiene hallazgos Clase A
abiertos que afecten su resultado o sus interfaces, satisface los cinco criterios
anteriores, y declara explícitamente sus límites Clase B. Un modelo con datos o
métodos ilustrativos puede alcanzar Platino como material educativo; no puede
presentarse por ello como cálculo profesional o regulatorio vigente.

## Veredicto

Como laboratorio educativo abierto, la base es sólida: arquitectura limpia,
disciplina de `Decimal`, configuración regulatoria versionada, y una suite de rigor
de identidades actuariales real (`tests/unit/test_actuarial_rigor.py`, ~336
verificaciones numéricas). La capa de honestidad (datos ilustrativos, avisos, y el
"no sustituye una nota técnica") es correcta.

El riesgo mayor estaba en la identidad declarada del proyecto — *cada modelo lleva la
identidad/contraste/límite que lo hace confiable*. Varias funciones de "verificación" e
"incertidumbre" eran tautológicas o estaban mal etiquetadas, y existía un conjunto de
defectos reales que entregaban números equivocados o rechazaban entradas válidas.

**Cierre (2026-07-25).** Los diez hallazgos Clase A están corregidos, cada uno con una
prueba cuyo valor esperado procede de una fuente externa, una identidad actuarial o un
cálculo a mano, y no de repetir la fórmula bajo prueba. La capa de confianza — que era
la más débil — ahora reproduce resultados publicados: Mack (1993) sobre el triángulo de
Taylor & Ashe da la reserva y el error estándar del artículo original al peso, y el
bootstrap ODP reproduce el parámetro de dispersión publicado para ese mismo triángulo.

Dos correcciones **a la auditoría misma**, ambas registradas abajo: el oráculo que
proponía para A10 era incorrecto, y su afirmación de que repetir el último factor
"sobreestima sistemáticamente" no se sostiene. Que la revisión también se revise es
parte del estándar.

Lo que **no** cambió: los techos Clase B. La mortalidad sigue siendo sintética y los
factores de RCS siguen siendo heurísticas pedagógicas, así que un resultado ahora
verificado sigue sin ser un resultado profesionalmente válido. El
[inventario Clase B](#inventario-clase-b-fase-5) los enumera uno por uno con su ruta de
sustitución.

## Clase A — defectos reales

### A1. `ratio_solvencia` con dos definiciones invertidas — Crítica

- `src/suite_actuarial/core/models/regulatorio.py:236` (usado por `AgregadorRCS` y
  la API en `src/suite_actuarial/api/routers/regulatory.py:164`): `RCS / capital`
  → solvente implica ratio **< 1**.
- `src/suite_actuarial/reportes/models.py:236`: `capital_disponible / RCS` →
  solvente implica ratio **≥ 1**.

La convención de industria/CUSF/Solvencia II es la segunda (fondos propios ÷ RCS,
≥100% = solvente). La API expone la versión invertida: una aseguradora sana reporta
"0.5". Las pruebas `tests/unit/test_rcs_completo.py:333,354` fijan la orientación
equivocada. Definir la cantidad una sola vez en `core/` y que todas las superficies
la importen. Corregir también el fallback `capital=0 → 999.99`, semánticamente
invertido bajo la definición actual.

### A2. El bootstrap no es England-Verrall/ODP y su distribución es incoherente — Crítica

`src/suite_actuarial/reservas/bootstrap.py`.

- Residuales calculados sobre el triángulo **acumulado** (deben ser sobre
  incrementales); `bootstrap.py:71-142`.
- Los valores ajustados no reproducen la diagonal observada → residuales
  correlacionados por fila, no de media cero.
- Sin parámetro de dispersión φ, sin corrección por grados de libertad, sin paso de
  varianza de proceso.
- Ruido arbitrario `np.random.normal(0, 0.05)` inyectado en `bootstrap.py:186-188`.
- La estimación central usa la **mediana** (`bootstrap.py:315`), no la media, así
  que no concilia con Chain Ladder.

Evidencia (seed 42, 2000 sims): reserva CL base 2062 → media bootstrap 5299 (2.5×),
CV 1.40, percentiles bimodales. Remediar: implementar un bootstrap ODP correcto, o
retirarlo de la superficie de confianza y reetiquetarlo como banda ilustrativa.

### A3. La configuración de XL rechaza capas válidas — Mayor

`src/suite_actuarial/core/models/reaseguro.py:241` (`validar_limite_mayor_retencion`).
Fuerza `limite > retencion`, pero el ancho de capa (`limite`) y la prioridad
(`retencion`) son independientes. La capa canónica **"5M xs 5M" lanza `ValueError`**;
también "5 xs 10", "10 xs 20". Sin base actuarial. La matemática de capado por
siniestro sí es correcta (`excess_of_loss.py:52-90`, verificada a mano); solo el
gate de configuración está mal. Eliminar la restricción.

### A4. Reinstalaciones nunca aplicadas en XL — Mayor

`src/suite_actuarial/reaseguro/excess_of_loss.py:92,202`. La recuperación
multi-siniestro erosiona un único límite compartido entre todas las ocurrencias;
`numero_reinstatements` y `modalidad` solo afectan el despliegue. Ejemplo: 5M xs 5M
con 1 reinstalación y dos pérdidas de 12M cede 5M cuando debería ceder 10M.
Subestima sistemáticamente la cesión.

### A5. ä_x usado como esperanza de vida en retiro programado — Mayor

`src/suite_actuarial/pensiones/plan_retiro.py:329`.
`esperanza_vida ≈ int(ä_65) = 11`, cuando la e₆₅ curtate de la tabla es ≈17.2. El
retiro programado divide el saldo entre ~11 en vez de ~17. En consecuencia,
`comparar_modalidades` (`plan_retiro.py:344-383`) contrasta dos denominadores casi
idénticos y la comparación de modalidades es vacía por construcción. Usar la
esperanza de vida (Σ ₜpₓ), no el factor de anualidad descontado.

### A6. Sin ajuste 1/m (mensual) en anualidades — Mayor

`src/suite_actuarial/pensiones/renta_vitalicia.py:118` y
`src/suite_actuarial/pensiones/plan_retiro.py:283`. Las pensiones se pagan
mensualmente pero se valúan con la ä_x **anual** en vez de ä_x^(12) ≈ ä_x − 11/24.
Sesgo unidireccional de ~3.9%: primas únicas sobreestimadas, pensiones mensuales
subestimadas.

### A7. Beneficio de vida entera sin fondear y discontinuidad de reserva — Mayor

`src/suite_actuarial/vida/ordinario.py:143,256`. El pricing suma solo edades
x…ω−1 y nunca fuerza q_ω=1, así que la cohorte viva en ω nunca recibe pago (un
beneficio "GARANTIZADO" que no se fondea). La reserva fija `SA` en el año final,
mientras la fórmula prospectiva un año antes da ≈0.38·SA — un salto que el propio
método prospectivo no sostiene. Aplicar la convención de edad terminal (q_ω=1)
dentro del motor de pricing.

### A8. Credibilidad de Bühlmann deriva mal la VHM — Mayor

`src/suite_actuarial/danos/tarifas.py:60,182`. Bühlmann de riesgo único resta
`EPV/n` en vez de `EPV` (`:60`), infla la VHM y **sobreestima la credibilidad Z**.
Bühlmann-Straub (`:182`) resta una *media* de una *varianza* (dimensionalmente
inválido), con fallback que descarta la corrección. La estructura de Z alrededor es
correcta; el defecto está aislado en el estimador de VHM.

### A9. "Verificación" que no verifica — Mayor (integridad de auditoría)

- `src/suite_actuarial/vida/dotal.py:314,323,343`: las cuatro `verificaciones` son
  autocumplidas (`vp_total` se *define* como su propia descomposición; el principio
  de equivalencia compara un valor consigo mismo; las reservas se comparan contra
  constantes fijadas). No ejercitan el motor de pricing ni la recursión prospectiva.
- `src/suite_actuarial/reservas/diagnosticos.py:31`: "incertidumbre de Mack" agrupa
  todos los link ratios en una sola desviación estándar; no es la σ²ₖ/MSEP de Mack.

Ambas se exponen como la capa de confianza y dan falso aseguramiento —
contradiciendo la razón de ser del proyecto. Reemplazar por oráculos independientes.

### A10. Factor de cola = último factor de desarrollo — Mayor

`src/suite_actuarial/reservas/chain_ladder.py:122`. Con `calcular_tail_factor=True`,
`tail = factores[-1]` repite el último factor una vez más y multiplica cada ultimate.
No es estimación de cola (ajuste de curva / benchmark); fabrica desarrollo sin base.

### Correcto y verificado (crédito donde corresponde)

Chain Ladder y Bornhuetter-Ferguson (verificados celda a celda), fórmulas de riesgo
colectivo `E[S]`/`Var[S]` y parametrizaciones de severidad, Quota Share, capado por
capa en XL, Stop Loss, identidades de conmutación (`ä₆₅ = N₆₅/D₆₅` verificada),
pricing temporal/dotal y reservas prospectivas de vida, cascada de reclamo GMM.

## Clase B — simplificaciones declaradas (techos profesionales)

- **Mortalidad sintética.** `src/suite_actuarial/data/mortality_tables/emssa_09.csv`
  es una rampa lineal
  de qx (no Gompertz; q₆₅≈0.0135 vs EMSSAH real ≈0.02), marcada
  `data_status: illustrative`. Toda cifra de vida/pensiones/anualidades descansa en
  mortalidad no-experiencia.
- **RCS son heurísticas inventadas.** `regulatorio/rcs_vida.py` (factores 0.003,
  rampas por edad) y ambas matrices de correlación son pedagógicas, no el modelo
  estocástico de la CNSF (declarado). Nota de robustez: la agregación var-cov
  (`agregador_rcs.py`, `rcs_vida.py`) asume matriz PSD; una correlación negativa con
  componentes grandes podría producir raíz de número negativo (error de dominio).
- **Margen de riesgo = 6% × mejor estimación** (`actuarial/valuation.py:145`) no es
  el margen Costo-de-Capital (6% × Σ SCR futuros descontados). La mejor estimación
  por póliza se piso en 0, lo que bloquea el BE negativo legítimo de negocio rentable.
- **Ley 97 renta vitalicia mono-vida** — omite el seguro de sobrevivencia exigido por
  la LSS-1997. **Ley 73 ignora el nivel salarial** (Art. 167). **GMM/accidentes sin
  frecuencia-severidad ni tendencia médica** pese al docstring; `siniestralidad =
  prima/(1+margen)` es circular.
- **Menores:** RRC pro-rata (declarada deprecada); redondeo tras cada factor en
  tarifas; `resultado_neto_cedente` con semántica distinta en QS vs XL; auto tarifica
  la RC de terceros sobre el valor del propio vehículo; tablas IMSS definidas pero no
  usadas (cuota social, pensión garantizada por semanas) con sustitutos hardcodeados.

## Inventario Clase B (fase 5)

Cada renglón nombra el dato o supuesto, su fuente, su vigencia, en qué consiste la
simplificación, dónde se avisa y qué haría falta para sustituirlo. Un modelo con
renglones abiertos aquí puede ser Platino **como material educativo**; no puede
presentarse como cálculo profesional o regulatorio vigente.

| Modelo / dato | Fuente | Vigencia | Simplificación | Dónde se avisa | Ruta de sustitución |
| --- | --- | --- | --- | --- | --- |
| Tabla de mortalidad `emssa_09.csv` | Ninguna: construida para el laboratorio | No aplica | Rampa lineal de qx, no Gompertz; q₆₅ ≈ 0.0135 contra ≈0.02 de la EMSSAH real | `data_status: illustrative` declarado en `metadata.json` y verificado al cargar: el único camino de carga es el paquete instalado, en modo estricto, con el sha256 declarado comprobado contra el archivo (`tests/unit/test_tablas_integridad.py`); los benchmarks publicados en `docs/VALIDATION.md` quedan sujetos por `tests/unit/test_validation_benchmarks.py`. Todo producto de vida y pensiones que la use reporta `validation_tier: experimental` | Licenciar la EMSSA-09 publicada, colocarla en el paquete de datos y actualizar su `content_hash`; el cargador ya rechaza cualquier CSV que no coincida con su declaración. Tras sustituirla, recalcular y volver a publicar los benchmarks, no reajustarlos para pasar |
| Convención de edad terminal | Supuesto del motor de pricing | Vigente | EMSSA-09 publica `q_100 = 0.442` (H); el pricing vitalicio **impone** `q_ω = 1` para fondear el beneficio | Docstring de `_qx_con_edad_terminal`; parámetro `omega_convention` en `calcular_lx` | Usar una tabla que cierre en 1, o declarar la edad terminal del producto |
| Factores de RCS (`rcs_vida.py`, `rcs_danos.py`) | Heurísticas pedagógicas (0.003, rampas por edad) | No aplica | No es el modelo estocástico de la CNSF | `ExperimentalModelWarning` al construir; `validation_tier` | Implementar el modelo CNSF vigente con su calibración publicada |
| Matrices de correlación RCS | Pedagógicas | No aplica | Se asume PSD sin verificarlo: una correlación negativa con componentes grandes puede dar raíz de negativo | Declarado en esta auditoría | Verificar PSD al cargar la configuración y rechazar matrices inválidas |
| Margen de riesgo (`valuation.py`) | 6% × mejor estimación | No aplica | No es Costo-de-Capital (6% × Σ SCR futuros descontados) | Docstring del módulo | Proyectar SCR futuros y descontarlos |
| Piso `BE ≥ 0` por póliza | Decisión de implementación | Vigente | Bloquea la mejor estimación negativa legítima de negocio rentable | Esta auditoría | Permitir BE negativo y agregarlo con su signo |
| Renta vitalicia Ley 97 | LSS-1997 | Vigente | Mono-vida: omite el seguro de sobrevivencia que la ley exige | `ExperimentalModelWarning` de pensiones | Modelar el beneficio conjunto y de sobrevivientes |
| Pensión Ley 73 | LSS-1973, Art. 167 | Vigente | Ignora el nivel salarial | `ExperimentalModelWarning` de pensiones | Incorporar la tabla del Art. 167 por rango salarial |
| Retiro programado | Práctica CONSAR | Vigente | Reparte `saldo / e_x` sin acreditar el rendimiento del saldo remanente: conservador | Docstring de `calcular_retiro_programado` (A5) | Dividir entre una anualidad cierta de `e_x` años a la tasa del fondo y recalcular cada año |
| Corrección 1/m | Woolhouse, primer término | Vigente | Falta el segundo término, `−(m²−1)/(12m²)·(δ + μ_x)` | Docstring de `ax_m` (A6) | Añadir el segundo término con `δ` y `μ_x` de la tabla |
| GMM y accidentes | Docstring del módulo | No aplica | Sin frecuencia-severidad ni tendencia médica; `siniestralidad = prima/(1+margen)` es circular; el sexo se captura pero no altera la prima | `ExperimentalModelWarning` al construir (2026-08-02; antes esta columna citaba un aviso que no existía); `disclaimer` y `validation_tier` en la respuesta del API | Modelar frecuencia y severidad con datos de experiencia |
| Credibilidad (Bühlmann y Bühlmann-Straub) | Supuesto Poisson `Var = media` | Vigente | Con un solo riesgo la EPV no se separa nonparametricamente de la VHM, así que se **asume** | Comentarios del estimador (A8) | Estimar EPV y VHM a partir de **varios** riesgos del portafolio |
| Prima de reinstalación XL | Práctica de mercado | Vigente | Pro rata a la cantidad al 100%; sin prorrateo temporal ni tasas escalonadas | Docstring de `calcular_prima_reinstalacion` (A4) | Parametrizar tasa por reinstalación y prorrateo a tiempo |
| Factor de cola (Sherman) | Sherman (1984) | Vigente | Es extrapolación; con `b ≤ 1` la serie no converge y el valor depende del horizonte | `ExperimentalModelWarning`, `tail_ajuste_r2`, `tail_horizonte`, `tail_serie_converge` (A10) | Declarar la cola con un benchmark de industria documentado |
| Bootstrap ODP y Mack | England-Verrall (1999), Mack (1993) | Vigente | Miden error **condicionado al Chain Ladder**: no cubren riesgo de modelo, mezcla, inflación no observada ni cola | `ALCANCE` en el resultado; `DISCLAIMER_MACK` (A2, A9a) | No hay sustitución simple: es un límite del método, no de la implementación |
| RRC pro-rata | Declarada deprecada | Deprecada | Método pro-rata simple | Docstring del módulo | Migrar al método vigente de reservas técnicas |
| Prima neta en la Reserva Matemática | Principio de equivalencia sobre la tabla cargada, o prima suministrada por quien llama | Teoría estándar (Bowers et al., *Actuarial Mathematics*, cap. 6-7) | Es prima NETA: sin gastos de adquisición ni administración, sin caducidad ni rescates, sin Zillmer ni margen de riesgo. La reserva resultante no es la reserva institucional de S-11.4 | `DISCLAIMER_RM`, emitido como `ExperimentalModelWarning` al construir `CalculadoraRM` y publicado en `ResultadoRM.disclaimer`; docstring del módulo (2026-08-02: el módulo se reescribió, ver CHANGELOG) | Requiere la nota técnica registrada con su estructura de gastos, la tabla de caducidad de la cartera y el método de valuación aprobado |
| Renta vitalicia dentro de `CalculadoraRM` | Anualidad anticipada ANUAL hasta la edad terminal de la tabla, aplicada a 12 × renta mensual | Convención del propio módulo | La renta mensual se valúa como anual anticipada; sin la corrección de Woolhouse (≈ 11/24 de un pago), el valor presente queda sobreestimado. Sesgo conservador para la reserva, pero sesgo | Docstring de `_calcular_renta_vitalicia` | Usar `pensiones.renta_vitalicia` / `TablaConmutacion.ax_m`, que sí aplican el ajuste de fraccionamiento |
| Edad terminal ω de la Reserva Matemática | Última edad publicada por la tabla cargada, con q_ω forzada a 1 | Convención auditada de `_qx_con_edad_terminal` (hallazgo A7) | El alcance de la cobertura queda acotado por el alcance de la tabla (ω = 100 para la EMSSA-09 empaquetada), no por la longevidad real | Docstring de `CalculadoraRM`; campo `ResultadoRM.edad_terminal_tabla` | Exige una tabla con cierre en edad terminal declarado por su emisor |
| Ejemplos autoverificables (`examples/casos/`, `examples/labs/`) | Los propios scripts | Vigente | Se ejecutan en la suite (`tests/unit/test_examples.py`, 2026-08-02): sus 43 aserciones son un control efectivo, no una promesa del README. Que un ejemplo pase significa que sus identidades internas se cumplen con los supuestos Clase B que arrastra (mortalidad sintética, tarifas ilustrativas, factores RCS pedagógicos), no que sus cifras sean profesionalmente válidas | Los `ExperimentalModelWarning` de los módulos que ejercitan | Sustituir los supuestos Clase B subyacentes; los ejemplos heredan el techo de sus datos |
| Tarifas de auto | Tablas ilustrativas que reproducen la estructura de una tarifa, no valores AMIS evidenciables | No aplica | Redondeo tras cada factor; la RC de terceros se tarifica sobre el valor del propio vehículo | `ExperimentalModelWarning` al construir `SeguroAuto`; `DISCLAIMER` de `danos/auto.py` (incluye el de `tablas_amis.py`); `disclaimer` en la respuesta del API | Redondear solo al final; tarificar RC sobre límite de responsabilidad |
| Seguro de incendio (`danos/incendio.py`) | Ninguna: tasas y factores construidos para el laboratorio | No aplica | Producto de factores sobre el valor declarado: sin deducible, sin regla proporcional/infraseguro, sin distinguir edificio de contenidos, sin riesgo catastrófico (sismo, hidrometeorológico) | `ExperimentalModelWarning` al construir; `DISCLAIMER` del módulo; `disclaimer` y `validation_tier` en la respuesta del API | Tarificar con experiencia siniestral propia y añadir un modelo de catástrofe separado |
| Seguro de RC general (`danos/rc.py`) | Ninguna: tasas por clase de actividad construidas para el laboratorio | No aplica | Prima por millar del límite: sin frecuencia ni severidad, sin medida de exposición y sin desarrollo de cola larga; el factor de deducible es escalonado sin interpolar | `ExperimentalModelWarning` al construir; `DISCLAIMER` del módulo; `disclaimer` y `validation_tier` en la respuesta del API | Tarificar sobre exposición con experiencia propia e interpolar el factor de deducible o declararlo tarifa escalonada |
| Accidentes y Enfermedades (`salud/accidentes.py`) | Ninguna: tasas, factores de ocupación y porcentajes de pérdidas orgánicas construidos para el laboratorio | No aplica | Prima = (SA/1000) × tasa × factor de ocupación, sin frecuencia ni severidad, sin gastos ni margen explícitos | `ExperimentalModelWarning` al construir; `DISCLAIMER` del módulo; `disclaimer` y `validation_tier` en la respuesta del API | Sustituir tasas y porcentajes por los del condicionado y la experiencia propia |
| Prima de Stop Loss (`reaseguro/stop_loss.py`) | «Tasa típica» del módulo | Sin verificar | `calcular_prima_reaseguro` fija 3% de las primas sujetas sin relación con la cartera; la prima de XL es burning cost simplificado con la tasa que da el usuario | Docstrings de ambos módulos; aviso en las pestañas de Reaseguro de Streamlit (2026-08-02) | Estimar la prima con la distribución de la siniestralidad agregada o con experiencia histórica |
| Tablas IMSS | Definidas en `tablas_imss.py` | Vigentes | Cuota social y pensión garantizada por semanas están definidas pero **no** se usan; hay sustitutos hardcodeados | Esta auditoría | Conectar las tablas al cálculo y borrar los sustitutos |
| `resultado_neto_cedente` | Convención interna | Vigente | Semántica distinta en Quota Share y en XL | Esta auditoría | Definir la cantidad una sola vez en `core/`, como se hizo con `ratio_solvencia` |
| Tasas de retención ISR (`validador_retenciones.py`) | Ninguna verificada | Sin verificar | 10% rentas vitalicias, 20% retiros de ahorro, 10% otros ingresos: cifras heredadas del desarrollo inicial, sin fuente en el repositorio | Docstring de la clase; `disclaimer` en la respuesta del API; aviso en la pestaña Retenciones | Leer el texto vigente de la LISR en diputados.gob.mx/DOF y fijar cada tasa con su cita y un test cuyo valor esperado venga del estatuto |
| Citas LISR Art. 145 y Art. 158 (retenciones) | Docstring del módulo | Sin verificar | Los números de artículo no se confirmaron contra el texto vigente; la numeración pudo cambiar por reformas | Docstring de la clase (2026-07-26) | Verificar contra el texto consolidado y corregir la cita |
| Cita LISR Art. 151 fracc. V (planes de retiro) | LISR, texto vigente consolidado (Cámara de Diputados), última reforma DOF 01-04-2024, consultada 2026-08-02 | Vigente | Verificada contra el estatuto: la fracción V es la correcta y el porcentaje propio es 10% de los ingresos acumulables (antes 15%). Los «cinco salarios mínimos elevados al año» se leen como cinco UMA anuales por el decreto de desindexación (DOF 27-01-2016): esa lectura es una interpretación, no texto expreso de la LISR | Encabezado de `validador_primas.py`; `TestFraccionVPlanesDeRetiro` | Ninguna acción pendiente sobre la cita; si el SAT publica criterio distinto sobre la equivalencia salario mínimo/UMA, reabrir |
| Tope global de deducciones personales (GMM, persona física) | LISR Art. 151, último párrafo (misma fuente y fecha de consulta) | Vigente | Implementado: menor entre 5 UMA anuales y 15% del total de ingresos. Dos límites residuales: (1) el tope es **global** sobre todas las deducciones personales del ejercicio y este módulo lo aplica a una prima aislada, de modo que el monto deducible es una cota superior; (2) sin `ingresos_totales_anuales` solo se aplica la rama de 5 UMA | Campos `tope_global` y `nota_tope_global` del resultado y de la respuesta del API; `TestTopeGlobalArt151` | Aceptar la suma de deducciones personales del ejercicio como insumo para topar el total, no una prima a la vez |
| Requisitos no cuantitativos de la fracción VI (beneficiario y medio de pago) | LISR Art. 151, fracc. VI | Vigente | La fracción VI condiciona la deducción a que el beneficiario sea el contribuyente, su cónyuge, concubino, ascendientes o descendientes en línea recta. El validador no verifica esa relación para persona física: solo marca `metodo_pago` como factor faltante | `factores_faltantes` y estado `indeterminate` del resultado | Exigir `relacion_beneficiario` también para persona física y rechazar las relaciones fuera de la lista |
| Cobertura temporal de los perfiles regulatorios | `config/config_<anio>.py` (INEGI/DOF/CNSF) | Vigente hasta 2027-01-31 | Los perfiles empaquetados cubren del 2024-02-01 al 2027-01-31. Fuera de ese rango no hay respuesta: `ConfiguracionNoDisponibleError`, 503 en los endpoints regulatorios y 422 en `/config/fecha/{fecha}`. No se extrapolan parámetros | Mensaje del error, detalle HTTP, `tests/unit/test_config_loader.py` | Agregar `config/config_2027.py` con los valores publicados y su fuente cuando existan |
| `requiere_retencion_forzosa` | Parámetro del módulo | Vigente | La rama que lo consume está al final de la cadena `elif`: solo es alcanzable para pensiones sin renta vitalicia; para los demás tipos no tiene efecto | Docstring de la clase; `description` del campo en el API | Reordenar la cadena si el efecto pretendido es forzar retención sobre pagos exentos |

## Temas sistémicos

1. **La capa de confianza es la más débil.** Para un proyecto cuya tesis es
   *modelos auto-verificables*, tener verificaciones tautológicas (A9), un bootstrap
   roto (A2) y una SE de Mack falsa es lo más importante a corregir.
2. **Sin fuente única de verdad para definiciones.** `ratio_solvencia` (A1) y
   `resultado_neto_cedente` significan dos cosas contradictorias en el mismo código.
   Definir cada cantidad actuarial una vez, en `core/`.
3. **Las pruebas confirman el código, no la verdad actuarial, en la capa
   regulatoria.** Los tests de RCS afirman `> 0` / `< 1.0` y *codifican* el ratio
   invertido. Faltan oráculos numéricos independientes donde los parámetros son
   inventados.
4. **Validación de entrada excesiva.** A3 (XL) y el piso BE≥0 rechazan/distorsionan
   entradas actuariales legítimas. Los validadores deben restringir lo imposible, no
   lo meramente inusual.

## Orden de remediación

Este es el trabajo siguiente. Cada punto debe cerrar conforme al
[Estándar Platino](#estándar-platino-y-regla-de-cierre); no basta una prueba que
replique el código corregido.

| Fase | Estado | Resultado exigido | Hallazgos | Criterio de salida |
| --- | --- | --- | --- | --- |
| 0. Contención de verdad | Cerrada (2026-07-25) | Ninguna interfaz llama “verificación”, “Mack” o “bootstrap ODP” a una cifra que no cumple esa definición. Ocultar la salida o mostrarla como ilustrativa mientras se corrige. | A2, A9, A10 | Prueba de contrato y texto de limitación visibles en cada superficie afectada. |
| 1. Definiciones y entradas | Cerrada (2026-07-25) | Una sola definición de solvencia; capas XL actuarialmente válidas aceptadas. | A1, A3 | Casos de borde, API/reporte coherentes y migración documentada para el ratio. |
| 2. Reservas y confianza | Cerrada (2026-07-25) | Bootstrap ODP y Mack correctos, con oráculos independientes; si no hay implementación defendible, la funcionalidad permanece ilustrativa y fuera de toda superficie de confianza. | A2, A9, A10 | Reproducción de un triángulo de referencia, semilla reproducible y conciliación explícita de estimador central. |
| 3. Beneficios de vida y pensiones | Cerrada (2026-07-25) | Flujos terminales, esperanza de vida y frecuencia de pago coherentes con el beneficio descrito. | A5, A6, A7 | Cálculos manuales, límites de edad terminal y comparación de modalidades no tautológica. |
| 4. Reaseguro y tarifas | Cerrada (2026-07-25) | Reinstalaciones y credibilidad consistentes con sus definiciones. | A4, A8 | Escenarios multi-siniestro y muestras conocidas que distingan fórmula correcta de la defectuosa. |
| 5. Límites profesionales | Cerrada (2026-07-25) | Los techos Clase B siguen visibles, priorizados y no se confunden con cálculo vigente. | Clase B | Inventario por modelo: dato, fuente, vigencia, simplificación, aviso y ruta de sustitución. |

Las fases 0 y 1 bloquean una declaración Platino para las interfaces expuestas. Las
fases 2 a 4 bloquean la declaración Platino de los dominios afectados. La fase 5
bloquea cualquier afirmación de uso profesional, aunque los modelos educativos
puedan ser Platino bajo su alcance declarado.

**Estado al 2026-07-25.** Las seis fases están cerradas: los diez hallazgos Clase A
tienen fecha de cierre, prueba con oráculo independiente y límite residual declarado en
el registro de abajo, y la Clase B tiene su inventario por modelo. Suite en verde
(1,084 pruebas, `ruff check` limpio). Esto **no** convierte al repositorio en una
herramienta profesional: los techos del inventario Clase B siguen vigentes, empezando
por la mortalidad sintética y las heurísticas de RCS, de los que dependen casi todas
las cifras de vida, pensiones y capital.

### Registro de cierre

Al cerrar cada hallazgo, sustituir `Pendiente` por la fecha y completar esta tabla.
No borrar el hallazgo: conservarlo como evidencia de revisión y enlazar el cambio.

**Corrección de esta auditoría (2026-07-25), oráculo de A10.** El hallazgo A10 exigía que
una estimación de cola sobre factores 1.5, 1.2 y 1.05 diera "estrictamente menor que
1.05". Esa expectativa es **incorrecta**: trata la cola como si fuera el siguiente factor,
cuando es el producto de **todos** los periodos restantes. Ajustando la curva de Sherman a
ese patrón se obtiene `f(k) = 1 + 0.5689·k^−2.0126` (r² = 0.93), cuyo producto extrapolado
desde el periodo 4 vale 1.1626 — ya supera 1.05 en el periodo 5. Se sigue de aquí que
repetir el último factor **subestimaba** este patrón, en contra de lo que afirmaba el
hallazgo ("sobreestima el ultimate de forma sistemática"): repetir el último factor no
yerra en una dirección fija, yerra en la que le toque, porque no es una estimación.
`tests/unit/test_cola.py::test_la_cola_no_es_comparable_con_el_ultimo_factor_observado`
demuestra ambas direcciones con curvas de decaimiento lento y rápido.

**Corrección de esta auditoría (2026-07-25).** Las filas A1 y A3 afirmaban que la prueba
de integración quedaba pendiente porque "`TestClient` no responde en este entorno". Era
falso: `.venv/bin/python -m pytest tests/integration` corría en verde. La causa real era
`tests/conftest.py`, que envolvía el import de `TestClient` **y** el de
`suite_actuarial.api.main` en un solo `try/except ImportError: pytest.skip(...)`; con un
intérprete sin los extras de API (como el del sistema, que es lo que resuelve un `pytest`
a secas) las 71 pruebas de integración se saltaban en silencio, y cualquier `ImportError`
real del paquete API degradaba a *skip* en vez de fallar. Corregido: el import de `app`
está fuera del `try` y `SUITE_REQUIRE_API=1` convierte el *skip* en fallo.

| Hallazgo | Estado | Prueba/oráculo independiente | Fuente o justificación | Límite residual |
| --- | --- | --- | --- | --- |
| A1 | Cerrado (2026-07-25) | `tests/unit/test_rcs_completo.py` contrasta capital / RCS; `tests/integration/test_api_regulatory.py::TestRCS` fija la orientación con tres oráculos independientes de magnitud: escala (duplicar capital duplica el ratio; la definición invertida lo reduciría a la mitad), frontera (capital = `rcs_total` ⇒ ratio 1.0 y cumplimiento) e insuficiencia (medio capital ⇒ ratio 0.5, excedente negativo) | Convención capital disponible / RCS, ≥100%; usada también por reportes | Los factores de RCS siguen siendo heurísticas pedagógicas (Clase B): el ratio está bien orientado pero su denominador no es el modelo CNSF. Capital cero se rechaza en la frontera (422): el ratio no está definido ahí. |
| A2 | Cerrado (2026-07-25) | `tests/unit/test_bootstrap.py`. Oráculos independientes: (a) **phi = 52,601** sobre el triángulo de Taylor & Ashe, el valor publicado del modelo ODP para ese triángulo — reproducirlo exige correctos el ajuste hacia atrás, los residuales sobre incrementales y los grados de libertad `n − p` con `p = I + J − 1`; (b) los incrementales ajustados reproducen **exactamente** las sumas por fila y por columna del observado, identidad algebraica del estimador máximo-verosímil del ODP, verificable sin simular; (c) el error de predicción (CV 15.9%) queda por encima del de Mack (13.1%) y por debajo del doble, contraste cruzado entre dos métodos independientes; (d) sobre un triángulo exactamente multiplicativo phi = 0 y la distribución colapsa en un punto | England y Verrall (1999), *Insurance: Mathematics and Economics* 25; England (2002), corrección por grados de libertad | La distribución es **condicional al modelo**: patrón de desarrollo estable y varianza proporcional a la media. No cubre riesgo de modelo, cambio de mezcla, inflación no observada ni cola. Hallazgo nuevo, **medido y documentado**: la media de las réplicas queda ~1% por encima de la reserva Chain Ladder y **no es error de Monte Carlo** — la reserva es convexa en los factores, así que remuestrearlos eleva la media (Jensen); el efecto persiste con el paso de proceso apagado y se verificó en cinco semillas. Por eso `conciliacion_cl_relativa` se reporta en vez de afirmarse, y el estimador puntual defendible sigue siendo la reserva de Chain Ladder. Los incrementales negativos no admiten varianza Gamma: esas celdas se proyectan sin simular y se cuentan en `celdas_sin_varianza_proceso` |
| A3 | Cerrado (2026-07-25) | `tests/unit/test_excess_of_loss.py` acepta 5M xs 5M y 5M xs 10M; `tests/integration/test_api_reinsurance.py::TestExcessOfLoss` parametriza 5M xs 5M, 5M xs 10M y 10M xs 20M con recuperaciones calculadas a mano (capa agotada, capa parcial, siniestro en la prioridad exacta, siniestro bajo la prioridad) | El límite es ancho de capa; la retención es prioridad | El capado **por ocurrencia** es correcto. El agregado sigue mal: las reinstalaciones nunca se aplican (A4), así que con `numero_reinstatements > 0` la cesión multi-siniestro se subestima hasta la fase 4. |
| A4 | Cerrado (2026-07-25) | `tests/unit/test_excess_of_loss.py::TestExcessOfLossReinstatements` y `tests/integration/test_api_reinsurance.py::test_las_reinstalaciones_amplian_el_agregado`. Oráculo decisivo: el escenario exacto del hallazgo — 5M xs 5M con una reinstalación y dos pérdidas de 12M — cede **10M**, calculado a mano como 5M + 5M; con cero reinstalaciones la misma pareja cede 5M, y la parametrización sobre 0/1/2 reinstalaciones separa la mecánica correcta de la anterior, que devolvía 5M en las tres. Más: el tope por ocurrencia sigue vigente (una pérdida de 100M recupera 5M, no el agregado de 10M) y la prima de reinstalación es pro rata a la cantidad (media capa = media prima base) | Práctica de mercado: límite por ocurrencia y agregado `límite × (1 + reinstalaciones)`; prima de reinstalación pro rata a la cantidad al 100% | **Cambio de contrato público:** se eliminó `aplicar_reinstatement()` — las reinstalaciones se aplican solas conforme el agregado se erosiona, y el método manual daba a entender lo contrario. `limite_disponible` ahora es el **agregado** remanente, no una sola capa. Nuevos: `limite_agregado`, `calcular_prima_reinstalacion()` y las claves `limite_agregado` / `limite_por_ocurrencia` / `prima_reinstalacion` en `detalles`. `reinstatements_usados` pasó a ser propiedad derivada de la erosión. Simplificación declarada: no hay prorrateo **temporal** (pro rata a tiempo) ni tasas distintas de 100% por reinstalación sucesiva |
| A5 | Cerrado (2026-07-25) | `tests/unit/test_pensiones_conmutacion.py::TestEsperanzaDeVida` y `tests/unit/test_pensiones_plan_retiro.py`. Oráculos: (a) `e_0` calculada a mano sumando la tabla `lx` de la tabla sintética; (b) la recursión `e_x = p_x·(1 + e_{x+1})`, ruta distinta del mismo cálculo; (c) **identidad exacta**: con interés cero `ax = 1 + e_x`, que es lo único que hace coincidir las dos cantidades y por tanto lo que demuestra que con `i > 0` no son intercambiables. Con la tabla EMSSA-09 e_65 = 17.23 contra ax = 11.63, y el retiro programado automático coincide con el calculado con esperanza explícita de 17 años y difiere >45% del calculado con 11 | Esperanza de vida abreviada `e_x = Σ ₜpₓ`; Bowers et al., cap. 3 | La comparación de modalidades dejó de ser tautológica (renta vitalicia 9,532 contra retiro programado 7,467 sobre 1.5M a los 65). **Simplificación declarada**: el reparto es `saldo / e_x` sin acreditar el rendimiento del saldo remanente, así que es conservador; un modelo completo dividiría entre una anualidad cierta de `e_x` años a la tasa del fondo y recalcularía cada año. La mortalidad sigue siendo sintética (Clase B) |
| A6 | Cerrado (2026-07-25) | `tests/unit/test_pensiones_renta_vitalicia.py::TestCorreccionFraccionamiento`. Oráculos: (a) el ajuste es la fracción exacta `11/24`, contrastada como fracción y no como decimal redondeado; (b) con `m = 1` la anualidad fraccionada **es** la anual, así que la corrección no altera el caso que no le corresponde; (c) identidad `10|a_55 = a_65 · ₁₀E₅₅` con la corrección en ambos lados, que falla si se aplica a un solo tramo; (d) la reserva en t = 0 iguala la prima única en las tres modalidades | Aproximación 1/m de primer orden (primer término de Woolhouse): `a_x^(m) ≈ a_x − (m−1)/(2m)` | El sesgo corregido es ~3.8-5% según la edad, y es unidireccional en direcciones opuestas: la prima única **baja** y la pensión que un saldo compra **sube**. **Defecto adicional encontrado al corregir**: prima y reserva tenían definiciones duplicadas del factor de renta; al corregir solo la primera, la identidad reserva(0) = prima única se rompió y lo delató. Ahora ambas usan `_factor_en_inicio_de_pagos`. Límite vigente: falta el segundo término de Woolhouse, `−(m²−1)/(12m²)·(δ + μ_x)`, de segundo orden frente al 11/24 |
| A7 | Cerrado (2026-07-25) | `tests/unit/test_vida_ordinario.py`. Oráculos: (a) la **probabilidad total de pago cierra en 1** (antes 0.9927 a los 35 y 0.9917 a los 65: entre 0.73% y 0.84% de la cohorte nunca cobraba un beneficio declarado GARANTIZADO); (b) la reserva en la edad terminal vale `SA·v`, que es lo que la fórmula prospectiva produce sola con `q_ω = 1`, no el `SA` que antes se fijaba a mano; (c) el último incremento de reserva es del mismo orden que los cinco previos, así que la discontinuidad desapareció. Verificado además fuera de la suite que la **recursión de Fackler cierra a 0 en cada año hasta la edad terminal**, incluida la última | Convención de edad terminal `q_ω = 1`; Bowers et al., cap. 7 | La cobertura pasó a ser `x … ω` **inclusive** (antes `x … ω−1`), lo que sube A_x ~0.2-0.3%. EMSSA-09 publica `q_100 = 0.442` para hombres, así que la convención es un **supuesto declarado** del motor de pricing, no un dato de la tabla; `calcular_lx` mantiene su propio parámetro `omega_convention` para quien necesite la otra lectura |
| A8 | Cerrado (2026-07-25) | `tests/unit/test_danos_tarifas.py::TestCredibilidadOraculosNumericos`. Oráculo decisivo: sobre `x = [80, 90, 100, 110, 120]` (media 100, s² = 250) la VHM correcta es 250 − 100 = 150, luego k = 2/3 y **Z = 0.8824**; el estimador anterior restaba EPV/n = 20, daba VHM = 230 y **Z = 0.9200**. La prueba fija el valor correcto y además exige que el defectuoso quede fuera de tolerancia. Para Bühlmann-Straub, cuatro periodos de exposición 100 con tasas 1.00/1.50/0.90/1.60 dan, paso a paso a mano, variación ponderada 37, c = 300, VHM = 0.110833, k = 0.0282 y Z = 0.9726. Las pruebas previas del módulo solo verificaban `0 ≤ Z ≤ 1`, que se cumple igual con la fórmula defectuosa | `Var(X_i) = EPV + VHM`, así que la varianza muestral de una observación estima ambas y hay que restar la EPV completa; VHM insesgada de Bühlmann-Straub con `c = m − Σmᵢ²/m` | Se eliminó el fallback que sustituía la VHM no positiva por `varianza_proceso / c`, un número positivo arbitrario que devolvía credibilidad donde no la hay; ahora ese caso da Z = 0 y prima manual completa. **Supuesto declarado que persiste**: con un solo riesgo la EPV no se puede separar nonparametricamente de la VHM, así que ambos métodos **asumen** un modelo Poisson (`Var = media`). Es una hipótesis del módulo, no una identidad, y sólo es dimensionalmente coherente bajo lectura de frecuencia |
| A9a (Mack) | Cerrado (2026-07-25) | `tests/unit/test_mack.py`. Oráculo externo: el triángulo de **Taylor & Ashe (1983)**, el ejemplo publicado en el propio artículo de Mack. La implementación reproduce la reserva total **18,680,856**, el error estándar total **2,447,095**, el CV 13.1% y el error estándar de **cada uno de los diez años de origen**. Ese total exige las tres piezas que faltaban: σ̂ₖ por periodo, MSEP por año de origen y término de correlación — sin el término cruzado la agregación independiente da ~2.03M, y la prueba fija también esa cifra y la desigualdad. Más: sobre un triángulo exactamente multiplicativo σ̂ₖ = 0 y SE = 0 (donde la banda agrupada da un positivo grande), invarianza de escala del CV, y la regla de extrapolación de Mack acota el último σ por los dos anteriores | Mack (1993), *ASTIN Bulletin* 23(2) | Nuevo módulo `reservas/mack.py`; `MackUncertainty` ahora apunta a `ResultadoMack` y `calcular_mack_uncertainty` queda deprecado (ignora el argumento `reserva`, porque Mack deriva la suya con factores ponderados por volumen). `ChainLadder.calcular_mack` avisa si la configuración usa otro promedio. `banda_dispersion_link_ratios` **sobrevive** como señal cruda de estabilidad, con su límite declarado y una prueba que la contrasta contra Mack para que no se confundan. Límite del método: mide el error **condicionado al Chain Ladder** — no cubre riesgo de modelo, cambio de mezcla, inflación no observada ni la incertidumbre de una cola |
| A9b (dotal) | Cerrado (2026-07-25) | `tests/unit/test_actuarial_rigor.py::TestDotalVerificacionesSonIndependientes`. Oráculos: (a) conmutación — `SA·(A¹_{x:n̄} + ₙE_x) = (M_x − M_{x+n} + D_{x+n})/D_x`, ruta distinta del motor de bucles, coincide a 1.4e-16; (b) recursión de Fackler (Bowers cap. 7), retrospectiva contra una reserva prospectiva, coincide a 2.0e-28. Cada prueba además **demuestra que la verificación falla** bajo un defecto deliberado: omitir la pierna de supervivencia rompe la descomposición, una prima +1% rompe la equivalencia, y una reserva intermedia +2% rompe Fackler — que es el único de los cuatro que la detecta | Bowers et al., *Actuarial Mathematics*, cap. 7 (recursión de Fackler); identidades de conmutación ya verificadas en la suite de rigor | Las verificaciones prueban la **consistencia interna** del motor, no la calidad de los datos: la mortalidad sigue siendo sintética (Clase B), así que un resultado verificado no es un resultado profesionalmente válido. Se eliminaron los atajos `return 0` y `return SA` de `calcular_reserva`; la fórmula prospectiva produce ambos valores por sí sola. Contrato ampliado (aditivo): `VerificacionesDotalResponse` gana `recursion_fackler`, `diferencia_descomposicion` y `diferencia_recursion`. |
| A10 | Cerrado (2026-07-25) | `tests/unit/test_cola.py` y `tests/unit/test_chain_ladder.py::TestColaEstimada`. Oráculo: sobre factores generados **exactamente** por `f_k = 1 + a·k^(−b)` el ajuste recupera `a` y `b` con r² = 1, y la cola coincide con el producto analítico extrapolado, calculado en la prueba desde los parámetros conocidos de antemano — no desde los estimados. Más: monotonía en `b` (decaimiento más rápido ⇒ cola menor), la serie diverge con `b ≤ 1` y se demuestra que la cola depende del horizonte, y el módulo **se niega a extrapolar** cuando el patrón no lo sostiene | Sherman (1984), "Extrapolating, Smoothing and Interpolating Development Factors", *PCAS* LXXI | **El oráculo que pedía el hallazgo era incorrecto** (ver la corrección arriba): la cola es el producto de todos los periodos restantes, no el siguiente factor. Sigue siendo **extrapolación**: ningún dato del triángulo respalda ese tramo, y el aviso viaja con el resultado junto con `tail_ajuste_r2`, `tail_horizonte` y `tail_serie_converge`. Con `b ≤ 1` la serie no converge y la cifra **depende del horizonte de truncamiento** (100 periodos por omisión), lo que se avisa explícitamente. Casos en que el módulo prefiere fallar a inventar: menos de tres factores mayores que 1, o un ajuste con `b ≤ 0`; ambos piden `tail_factor` explícito. `validation_tier` vuelve a `supported`, y el desarrollo ya terminado se reconoce como tal (`sin_desarrollo_residual`) en vez de llegar a 1.0 por accidente |
