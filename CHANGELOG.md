# Changelog

## Unreleased — remediación de la auditoría actuarial (`docs/AUDIT.md`)

Las seis fases de la auditoría están cerradas: los diez hallazgos Clase A corregidos,
cada uno con una prueba cuyo valor esperado procede de una fuente externa, una
identidad actuarial o un cálculo a mano. Los techos Clase B siguen vigentes y ahora
tienen inventario por modelo, con fuente, vigencia y ruta de sustitución.

### Breaking — cambios numéricos silenciosos

Ninguno cambia el esquema de la API. Cambian el **valor** que devuelve un campo
existente, que es la ruptura más peligrosa: un cliente que no lea esta entrada no
notará nada.

- **Bootstrap (A2).** `POST /api/v1/reserves/bootstrap` es ahora el bootstrap ODP de
  England-Verrall. `reserva_total` es la **media** de las réplicas (antes la mediana) y
  concilia con Chain Ladder dentro de ~1%; antes quedaba 2.5× por encima. La dispersión
  pasó de ser una banda ilustrativa a un **error de predicción**: sobre el triángulo de
  Taylor & Ashe da CV 15.9%, comparable con el 13.1% de Mack. `validation_tier` sube de
  `illustrative` a `supported`.
- **Factor de cola (A10).** `calcular_tail_factor=True` estima la cola ajustando la
  curva de potencia inversa de Sherman (1984) y extrapolando el producto del desarrollo
  restante, en vez de repetir el último factor. Sobre un patrón 1.5 / 1.2 / 1.05 la cola
  pasa de 1.05 a 1.1626: repetir el último factor **subestimaba** este caso. Con
  desarrollo ya terminado la cola es 1.0 por reconocerlo, no por accidente.
- **Reaseguro XL (A4).** El agregado del periodo es `límite × (1 + reinstalaciones)` y
  el límite por ocurrencia es el ancho de la capa. "5M xs 5M con 1 reinstalación" frente
  a dos pérdidas de 12M cede **10M**, no 5M. Cualquier contrato con
  `numero_reinstatements > 0` y varios siniestros devuelve más recuperación que antes.
- **Pensiones (A5, A6).** El retiro programado divide entre la esperanza de vida
  `e_x = Σ ₜpₓ` (17.2 a los 65) y no entre `int(ax)` (11): la pensión **baja** ~35%. Las
  rentas mensuales llevan la corrección 1/m (`ax^(12) ≈ ax − 11/24`): la prima única
  **baja** ~4% y la pensión que un saldo compra **sube** ~4%.
- **Vida ordinario (A7).** La cobertura vitalicia llega a la edad terminal **inclusive**
  con `q_ω = 1`, así que `A_x` sube ~0.2-0.3% y el beneficio queda fondeado para toda la
  cohorte (antes entre 0.73% y 0.84% nunca cobraba). La reserva del último año pasa de
  `SA` fijado a mano a `SA·v`, que es lo que produce la fórmula prospectiva.
- **Credibilidad (A8).** Bühlmann resta la EPV completa, no `EPV/n`: sobre una muestra
  con media 100 y varianza 250, `Z` pasa de 0.9200 a 0.8824. Bühlmann-Straub deja de
  restar una media de una varianza. Ambos devuelven `Z = 0` — y prima manual completa —
  cuando la variación observada no supera a la de proceso.

### Cambios de contrato público

- **Eliminado** `ExcessOfLoss.aplicar_reinstatement()`. Las reinstalaciones se aplican
  solas conforme el agregado se erosiona; el método manual sugería lo contrario y en la
  práctica ninguna recuperación lo usaba. Sustitutos: `limite_agregado`,
  `calcular_prima_reinstalacion()` y las claves `limite_agregado`,
  `limite_por_ocurrencia` y `prima_reinstalacion` en `detalles`.
  `ExcessOfLoss.limite_disponible` ahora es el **agregado** remanente, no una sola capa,
  y `reinstatements_usados` es una propiedad derivada de la erosión.
- `calcular_mack_uncertainty(triangulo, reserva)` queda deprecado con
  `DeprecationWarning` y **ignora** el argumento `reserva`: Mack deriva la suya con
  factores ponderados por volumen, que es lo único con lo que su error estándar es
  coherente. Use `reservas.calcular_mack`. `MackUncertainty` ahora apunta a
  `ResultadoMack`.
- `detalles` del bootstrap: `desviacion_estandar` → `error_prediccion`; nuevas
  `phi_dispersion`, `grados_libertad`, `parametros_modelo`, `celdas_utilizables`,
  `ajuste_grados_libertad`, `conciliacion_cl_relativa`,
  `celdas_sin_varianza_proceso`. Desaparecen `tasa_descarte`, `intentos_descartados` y
  `simulaciones_fallidas`: el método ya no descarta réplicas.
- `detalles` de Chain Ladder con cola estimada: nuevas `tail_ajuste_r2`,
  `tail_ajuste_a`, `tail_ajuste_b`, `tail_horizonte`, `tail_periodos_ajustados` y
  `tail_serie_converge`.

### Métodos implementados

- **Mack (1993)** — `reservas/mack.py`. σ̂ₖ por periodo de desarrollo, MSEP por año de
  origen y término de correlación entre años. Validado contra el triángulo de
  Taylor & Ashe, el ejemplo publicado en el artículo original: reproduce la reserva
  18,680,856, el error estándar total 2,447,095 y el error de **cada** año de origen.
- **Bootstrap ODP de England-Verrall** — `reservas/bootstrap.py`. Residuales de Pearson
  sobre incrementales contra valores ajustados hacia atrás desde el ultimate, parámetro
  de dispersión φ con `n − p` grados de libertad, corrección de England (2002) y
  varianza de proceso Gamma. Reproduce φ = 52,601 para Taylor & Ashe. Los incrementales
  ajustados reproducen exactamente las sumas por fila y por columna del observado.
- **Curva de potencia inversa de Sherman (1984)** — `reservas/cola.py`. Ajuste log-lineal
  con r², horizonte de truncamiento explícito y aviso cuando la serie no converge
  (`b ≤ 1`). Se niega a extrapolar cuando el patrón no lo sostiene.
- **Esperanza de vida abreviada** — `TablaConmutacion.ex` y `lx`. Identidad de control:
  con interés cero, `ax = 1 + e_x`.
- **Corrección 1/m** — `TablaConmutacion.ax_m` y `ajuste_fraccionamiento`.
- **Convención de edad terminal** — `edad_terminal` en `calcular_seguro_vida` y
  `calcular_anualidad`.

### Defectos encontrados al corregir (no señalados por la auditoría)

- **Prima y reserva de renta vitalicia tenían definiciones duplicadas** del factor de
  renta. Al aplicar la corrección 1/m solo a la primera, la identidad
  `reserva(0) = prima única` se rompió y lo delató. Ahora ambas usan
  `_factor_en_inicio_de_pagos`.
- **La media del bootstrap ODP queda ~1% por encima de la reserva Chain Ladder y no es
  ruido de Monte Carlo**: la reserva es convexa en los factores de desarrollo, así que
  remuestrearlos eleva la media (Jensen). Verificado en cinco semillas y con el paso de
  proceso apagado. Se reporta en `conciliacion_cl_relativa` en vez de afirmarse.
- **El oráculo que la auditoría proponía para A10 era incorrecto**, y con él su
  afirmación de que repetir el último factor "sobreestima sistemáticamente". Ambas
  correcciones quedaron registradas en `docs/AUDIT.md`.

### Fases 0 y 1 (contención y definiciones)

- **Bootstrap (A2).** Se eliminó el ruido `np.random.normal(0, 0.05)`, la sustitución de
  réplicas fallidas por la reserva base — que apilaba una masa puntual — y el sesgo por
  selección de descartar triángulos no monótonos. Nuevo componente `AvisoIlustrativo` en
  el frontend, que se renderiza cuando la respuesta trae `validation_tier:
  "illustrative"`.
- **Verificaciones del dotal (A9b).** Las cuatro comprobaciones eran autocumplidas y
  ninguna podía fallar. Ahora cada una contrasta el motor contra una ruta independiente:
  funciones de conmutación `(M_x − M_{x+n} + D_{x+n})/D_x` para la descomposición, la
  salida real de `calcular_prima` para la equivalencia, y la recursión de Fackler para la
  trayectoria de reservas. Se eliminaron los atajos `return 0` y `return SA` de
  `calcular_reserva`.
  *Contrato ampliado (aditivo)*: `VerificacionesDotalResponse` y `DotalLabChecks`
  ganan `recursion_fackler`, `diferencia_descomposicion` y `diferencia_recursion`.
- `tests/conftest.py` ya no degrada un `ImportError` real del paquete API a un
  *skip*: solo se guarda el import de `TestClient`. Con `SUITE_REQUIRE_API=1`, una
  dependencia opcional faltante falla en vez de saltarse. La auditoría atribuía la
  ausencia de pruebas de integración de A1/A3 a que "`TestClient` no responde en
  este entorno"; la causa real era este `try/except`.
- Cerrados A1 (orientación del ratio de solvencia) y A3 (capas XL válidas) con
  pruebas de integración: escala, frontera e insuficiencia para el ratio;
  recuperaciones calculadas a mano para 5M xs 5M, 5M xs 10M y 10M xs 20M.

## 2.1.0 (2026-07-19)

- Added effective-dated regulatory profiles with source references, hashes,
  support tiers, and deterministic date loading.
- Corrected 2026 UMA to 117.31 daily / 3,566.22 monthly / 42,794.64 annual
  from 1 February, and IMSS Ley 97 transition weeks to 825/850/875.
- Corrected 2024/2025 UMA anual to the official INEGI figures 39,606.36 and
  41,273.52 (annual = monthly x 12 per Ley UMA Art. 4; previous values used
  daily x 365).
- Config coverage now ends at the last profile's effective_to (31 January
  2027), derived from the bundled profiles instead of a hardcoded date;
  dates outside coverage raise explicitly.
- cargar_config() without arguments now delegates to cargar_config_fecha(),
  so January dates resolve to the prior year's UMA on both public paths.
- Added auditable life cash-flow valuation, calculation metadata, Mack-style
  reserve diagnostics, and explicit experimental-model warnings.
- Fiscal validation now exposes eligible/not_eligible/indeterminate status;
  legacy boolean fields remain for compatibility.
- Added examples/casos/: seven self-verifying worked cases (one per domain)
  with realistic Mexican scenarios, asserted actuarial identities, and cited
  sources; fixed stale README/CLI usage snippets to match the real API.
- Added an interactive illustrative case to each frontend domain page: a
  concrete scenario with sliders that recalculate against the API in real
  time, followed by a technical reading of the result (ES/EN).
- Fixed Chain Ladder tail factor: manual and calculated tail factors were
  appended to the factor list but never applied, so ultimates and reserves
  ignored them; the tail now scales each projected ultimate (with tests).

## 2.0.0 (2026-03-22)

### Nuevo
- Dominio Danos: SeguroAuto con tablas AMIS, ModeloColectivo, credibilidad Buhlmann
- Dominio Salud: GMM con bandas quinquenales, AccidentesEnfermedades
- Dominio Pensiones: Conmutacion, RentaVitalicia, PensionLey73, PensionLey97 con tablas IMSS completas
- Sistema de configuracion regulatoria versionada (config_2024, config_2025, config_2026)
- Modulo de tasas de interes (CurvaRendimiento)
- Demo interactivo con 7 paginas Streamlit mostrando uso de la libreria

### Cambiado
- Renombrado paquete: mexican_insurance -> suite_actuarial
- Dividido validators.py (1297 lineas) en core/models/ submodulos
- Aplanado products/vida/ -> vida/, reinsurance/ -> reaseguro/
- RCS inversion usa correlacion 0.75 (antes 1.0 suma simple)
- RCS vida usa matriz de correlacion CNSF (antes correlacion cero)

### Corregido
- validador_siniestros.py: nombres de campo Pydantic incorrectos (crasheaba PM)
- Tasa de aportacion AFORE: 6.5% -> 10.775% (era 40% menor)
- reserva_matematica.py: soporte para tabla EMSSA-09 real + duracion de poliza
- UMA 2024 anual: 39628.08 -> 39628.05

## 1.0.0 (2026-03-18)
- Lanzamiento inicial con Vida, Reaseguro, Reservas, Regulatorio
- 307 tests, 87% cobertura
