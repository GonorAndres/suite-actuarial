---
title: "Suite Actuarial Mexicana: Tarificacion, Reaseguro, Reservas y Cumplimiento Regulatorio en Python"
description: "Libreria actuarial en Python con 6 fases: tablas EMSSA-09, primas de vida (temporal, ordinario, dotal), reaseguro (QS, XoL, SL), reservas (Chain Ladder, BF, Bootstrap), RCS bajo LISF, reportes CNSF y validaciones SAT. 307 tests, 87% cobertura, dashboard Streamlit interactivo."
date: "2026-03-19"
category: "proyectos-y-analisis"
lang: "es"
tags: ["Python", "Pydantic", "LISF", "CUSF", "CNSF", "RCS", "Reservas", "Chain Ladder", "Reaseguro", "Streamlit", "EMSSA-09", "SAT"]
---

# Suite Actuarial Mexicana: Tarificacion, Reaseguro, Reservas y Cumplimiento Regulatorio en Python

En el area tecnica de una aseguradora mexicana tipica, el ciclo operativo trimestral se fragmenta en hojas de calculo que no se comunican entre si. Un actuario tarifica con una tabla EMSSA-09 pegada en Excel, otro calcula reservas con un triangulo de desarrollo separado, un tercero alimenta el formato RCS a mano, y al final alguien intenta cuadrar todo para el reporte que se entrega a la CNSF. Cada trimestre, el mismo ejercicio de reconciliacion manual.

La **Suite Actuarial Mexicana** unifica esos flujos en una sola libreria Python. Cubre desde la tabla de mortalidad EMSSA-09 hasta el reporte trimestral CNSF, pasando por tarificacion de productos de vida, tres estrategias de reaseguro, metodos avanzados de reservas y validaciones fiscales del SAT. A diferencia de [SIMA](/proyectos-y-analisis/sima), que construye su propio modelo de mortalidad desde datos crudos del INEGI via Lee-Carter, esta suite utiliza directamente la tabla regulatoria EMSSA-09 y se enfoca en la amplitud del ciclo asegurador: productos, reaseguro, reservas, cumplimiento y reporteo.

## El Problema -- Por que una Suite Actuarial en Python

El mercado asegurador mexicano esta regulado por la Comision Nacional de Seguros y Fianzas (CNSF) bajo el marco de la Ley de Instituciones de Seguros y de Fianzas (LISF) y la Circular Unica de Seguros y Fianzas (CUSF). Este marco normativo impone requerimientos especificos que no existen en ninguna otra jurisdiccion: tablas de mortalidad propias (EMSSA-09), formatos de reporte trimestrales con estructura definida, calculo del Requerimiento de Capital de Solvencia (RCS) con parametros calibrados al mercado mexicano, y reglas fiscales de deducibilidad que dependen de la Ley del ISR.

La mayoria del trabajo actuarial en Mexico se realiza en Excel o en sistemas propietarios como Prophet o MoSes. Para aseguradoras medianas y chicas, los costos de licenciamiento de herramientas comerciales son prohibitivos, y el resultado suele ser una coleccion de hojas de calculo donde cada celda es un punto potencial de error. Existe software actuarial de codigo abierto en Python -- el paquete `chainladder` para reservas, `lifelines` para analisis de supervivencia -- pero ninguno integra los requisitos regulatorios mexicanos. No hay una libreria que sepa lo que es una EMSSA-09, que calcule el RCS conforme a la LISF, o que valide la deducibilidad de primas segun el articulo 151 de la LISR.

La suite llena ese hueco con dos decisiones de diseno fundamentales. La primera es usar Pydantic v2 como guardia de dominio: cada dato que entra al sistema -- edad del asegurado, suma asegurada, configuracion de producto, triangulo de siniestros -- se valida antes de que toque una formula. Un asegurado con edad negativa, una tasa de interes tecnico del 200%, o una suma asegurada de cero simplemente no entran al sistema. La segunda es usar `Decimal` en lugar de `float` en toda la cadena de calculo. En un contexto donde las diferencias de centavos se acumulan sobre carteras de miles de polizas, la precision aritmetica no es un lujo academico: es un requisito operativo.

## Productos de Vida -- Temporal, Ordinario, Dotal

### Arquitectura de productos

Todos los productos de la suite heredan de una clase base abstracta `ProductoSeguro` que define la interfaz comun: `calcular_prima()`, `calcular_reserva()`, `validar_asegurabilidad()` y `aplicar_recargos()`. El diseno combina dos patrones clasicos. El **Template Method** fija la secuencia de calculo -- validar asegurabilidad, calcular prima neta, aplicar recargos, construir resultado -- mientras que cada producto concreto implementa la logica especifica de su formula actuarial. El **Strategy** entra en los metodos de promedio para factores de desarrollo y las modalidades de reaseguro.

El metodo `aplicar_recargos()` vive en la clase base y descompone la prima comercial de manera transparente: gastos de administracion (5% por defecto), gastos de adquisicion (10%) y margen de utilidad (3%). Un `model_validator` de Pydantic verifica que los recargos totales no excedan el 100% de la prima neta, cortando de raiz configuraciones absurdas.

### La tabla EMSSA-09

La Experiencia Mexicana de Seguridad Social 2009 (EMSSA-09) es la tabla de mortalidad regulatoria para seguros de vida en Mexico. Cada registro contiene tres campos: edad, sexo y `qx`, la probabilidad de que una persona de edad `x` fallezca antes de cumplir `x+1` anos. Para un hombre de 35 anos, la tabla indica `qx = 0.001300`, es decir, 1.3 fallecimientos por cada mil personas de esa edad. A los 40, el valor sube a `qx = 0.001600`. Esta progresion de la mortalidad es el insumo fundamental de toda la tarificacion.

La suite carga la EMSSA-09 desde un CSV y la encapsula en un modelo `TablaMortalidad` que soporta interpolacion para edades intermedias y validacion automatica de que cada `qx` este entre 0 y 1.

### Formulas de tarificacion

La prima neta se calcula bajo el **principio de equivalencia**: el valor presente actuarial de los beneficios futuros debe igualar el valor presente actuarial de las primas futuras. Para un seguro temporal de `n` anos a un asegurado de edad `x`:

- **Seguro temporal** A[x:n]: Suma de v^(t+1) * t_p_x * q_(x+t) para t de 0 a n-1, donde v = 1/(1+i) es el factor de descuento a tasa tecnica i, t_p_x es la probabilidad de sobrevivir t anos, y q_(x+t) es la mortalidad a edad x+t.
- **Anualidad anticipada** a-doble[x:n]: Suma de v^t * t_p_x para t de 0 a n-1. Representa el valor presente de un peso pagado al inicio de cada ano mientras el asegurado sobreviva.
- **Prima neta nivelada**: P = A[x:n] / a-doble[x:n]. Es la cantidad anual constante que, pagada mientras el asegurado viva dentro del plazo, financia exactamente el beneficio esperado.

La tasa de interes tecnico es 5.5%, el maximo tipico que la CNSF permite para productos tradicionales de vida en Mexico.

### Ejemplo numerico concreto

Consideremos un hombre de 35 anos con suma asegurada de $1,000,000 MXN en un seguro temporal a 20 anos. Con la EMSSA-09 y tasa tecnica de 5.5%:

- La prima neta anual resulta aproximadamente $5,000 MXN. Este monto refleja que la probabilidad de muerte acumulada en 20 anos es relativamente baja para un hombre de 35 (qx arranca en 0.0013 y crece gradualmente).
- Los recargos suman 18% (5% admin + 10% adquisicion + 3% utilidad): alrededor de $900 MXN.
- La prima total anual queda en aproximadamente $5,900 MXN.

El desglose se almacena en un `ResultadoCalculo` validado por Pydantic, que incluye metadata con tabla utilizada, tasa, plazo y frecuencia de pago.

### Comparativa entre productos

| Aspecto | Temporal | Ordinario | Dotal |
|---|---|---|---|
| Cobertura | Plazo fijo (10, 20, 30 anos) | Vitalicia (hasta edad omega) | Plazo fijo |
| Pago por fallecimiento | Solo si muere en el plazo | Garantizado (cuestion de cuando) | Si muere en el plazo |
| Pago por supervivencia | No hay | No hay | Si, al vencimiento |
| Prima relativa | Baja (riesgo puro) | Media (pago garantizado) | Alta (ahorro + proteccion) |
| Reserva al vencimiento | Cero | Crece hasta la SA | Igual a la SA |
| Uso tipico | Proteccion familiar temporal | Planeacion patrimonial y sucesoria | Ahorro para educacion, retiro |

El seguro temporal es riesgo puro: si el asegurado sobrevive al plazo, no hay pago. El ordinario es vitalicio -- el pago esta garantizado, solo es cuestion de cuando. El dotal combina proteccion con ahorro: paga la suma asegurada ya sea por muerte o por supervivencia al vencimiento. Un padre de 30 anos que contrata un dotal a 20 anos con $500,000 MXN sabe que, pase lo que pase, habra $500,000 disponibles cuando su hijo cumpla la edad de ir a la universidad.

## Reaseguro -- Tres Estrategias de Transferencia de Riesgo

El reaseguro es el seguro de las aseguradoras. Cuando una compania tiene riesgos que exceden su capacidad de absorcion -- por monto individual, por concentracion o por volatilidad agregada -- transfiere parte de esos riesgos a un reasegurador a cambio de ceder parte de las primas. La suite implementa tres estrategias complementarias.

### Quota Share (Cuota Parte)

El contrato mas simple y predecible. El reasegurador acepta un porcentaje fijo de **todas** las polizas: si el contrato es 30% QS, recibe 30% de cada prima y paga 30% de cada siniestro. A cambio, paga una comision a la cedente (tipicamente 25%) por los gastos de adquisicion ya incurridos.

En la suite, un `QuotaShareConfig` valida que el porcentaje de cesion este entre 0 y 100, la comision no exceda 50%, y la vigencia del contrato no supere 5 anos. El calculo es directo: `prima_cedida = prima_bruta * (porcentaje_cesion / 100)`. La ventaja del QS es la simplicidad y la generacion de ingreso por comisiones. La desventaja es que cedes la misma proporcion de todos los riesgos, incluyendo los rentables.

### Excess of Loss (Exceso de Perdida)

Proteccion no proporcional contra siniestros grandes. El reasegurador interviene unicamente cuando un siniestro individual excede la retencion de la cedente, y paga hasta un limite maximo. La notacion estandar es "limite xs retencion": un contrato "500 xs 200" significa que la cedente retiene los primeros $200,000 y el reasegurador paga el exceso hasta $500,000 adicionales.

Si el siniestro es de $150,000, la cedente absorbe todo. Si es de $400,000, la cedente paga $200,000 y el reasegurador $200,000. Si es de $800,000, la cedente paga $200,000, el reasegurador paga los $500,000 de limite, y la cedente absorbe los $100,000 restantes.

La implementacion incluye **reinstatements**: la posibilidad de reinstalar el limite despues de usarlo, pagando una prima adicional. Un `model_validator` verifica que el limite sea mayor que la retencion -- una condicion que parece obvia pero que en hojas de calculo con celdas editables se viola con mas frecuencia de la que uno quisiera admitir.

### Stop Loss (Limitacion de Perdidas)

Proteccion agregada sobre toda la cartera. El Stop Loss se activa cuando la siniestralidad total (siniestros / primas) excede un umbral llamado **attachment point**. Un contrato "80% xs 20%" sobre $10M de primas sujetas significa: si la siniestralidad supera 80%, el reasegurador cubre hasta 20 puntos porcentuales adicionales. Si los siniestros suman $9M (90% de siniestralidad), el reasegurador paga $1M (el 10% de exceso sobre 80%, aplicado a $10M de primas). Si los siniestros llegan a $11M (110%), el reasegurador paga el maximo de $2M (20% de $10M).

Pydantic valida que el attachment point este en un rango razonable (50%-200%) -- puntos de activacion fuera de ese rango indican un error de captura, no un contrato real.

## Reservas Avanzadas -- Chain Ladder, Bornhuetter-Ferguson, Bootstrap

La estimacion de reservas para siniestros pendientes (IBNR -- Incurred But Not Reported) es uno de los problemas centrales de la practica actuarial en danos. Quien haya leido el [post sobre el Insurance Claims Dashboard](/proyectos-y-analisis/insurance-claims-dashboard) ya conoce la mecanica del Chain Ladder y los triangulos de desarrollo. Aqui no voy a repetir la explicacion desde cero. En cambio, quiero centrarme en tres aspectos que distinguen esta implementacion.

### Implementacion propia vs. paquete chainladder

La suite incluye `chainladder` como dependencia, pero implementa Chain Ladder desde cero en el modulo `reservas/chain_ladder.py`. La razon no es reinventar la rueda: es poder integrar las validaciones Pydantic en cada paso del proceso. El `ConfiguracionChainLadder` permite elegir entre promedio simple, ponderado o geometrico para los factores de desarrollo, y opcionalmente calcular un factor de cola (tail factor) para desarrollo tardio. Cada `ResultadoReserva` incluye un `model_validator` que verifica la identidad fundamental: ultimate = pagado + reserva. Si hay una inconsistencia mayor a un centavo, el modelo rechaza el resultado.

### Bootstrap y cuantificacion de incertidumbre

Chain Ladder produce una estimacion puntual. Bornhuetter-Ferguson la complementa ponderando con una expectativa a priori (loss ratio esperado), lo cual la hace mas estable para anos de origen recientes con poco desarrollo. Pero ninguno de los dos responde la pregunta mas importante: "que tan equivocada puede estar esta estimacion?"

El modulo Bootstrap responde con una distribucion completa. El proceso es:

1. Ejecutar Chain Ladder en el triangulo original (modelo base).
2. Calcular residuales de Pearson: (observado - esperado) / sqrt(esperado).
3. Re-muestrear esos residuales para generar N triangulos sinteticos (por defecto 1,000 simulaciones).
4. Ejecutar Chain Ladder en cada triangulo sintetico.
5. Obtener la distribucion de reservas posibles y calcular percentiles.

La diferencia entre el percentil 50 (mediana) y el percentil 75 revela la incertidumbre del proceso. Si P50 = $2.5M y P75 = $3.1M, hay un 25% de probabilidad de que la reserva necesaria sea al menos $600,000 mayor que la mediana. Esa diferencia es directamente relevante para la decision de cuanto capital mantener. En un `ConfiguracionBootstrap`, Pydantic valida que los percentiles solicitados esten entre 1 y 99, y que el numero de simulaciones este entre 100 y 10,000.

## Cumplimiento Regulatorio -- RCS, CNSF, S-11.4, SAT

Esta es la seccion que diferencia a la suite de cualquier otro paquete actuarial de codigo abierto. No existe, hasta donde he investigado, ninguna libreria publica que implemente el calculo del RCS mexicano, las reglas de la Circular S-11.4, o las validaciones fiscales del SAT para primas de seguros. Estos modulos requirieron la mayor investigacion con las menores referencias disponibles.

### RCS: Requerimiento de Capital de Solvencia

El RCS es el monto minimo de capital que una aseguradora debe mantener para absorber perdidas inesperadas con un nivel de confianza del 99.5% (equivalente al percentil 99.5 de la distribucion de perdidas a un ano). La suite calcula tres modulos de riesgo:

**Riesgo de suscripcion vida** (`RCSVida`). Cuatro subriesgos:
- *Mortalidad*: Los asegurados mueren antes de lo esperado. Formula: 0.3% de la suma asegurada total, ajustado por factor de edad (1.0 a los 30 anos, hasta 3.0 a edades avanzadas) y factor de diversificacion (disminuye con mas asegurados, por ley de grandes numeros).
- *Longevidad*: Los asegurados de rentas vitalicias viven mas de lo esperado. Formula: 0.2% de la reserva matematica, ajustado por edad y duracion promedio de polizas.
- *Invalidez*: Incapacidad del asegurado.
- *Gastos*: Los gastos de administracion exceden las proyecciones.

**Riesgo de suscripcion danos** (`RCSDanos`). Dos subriesgos:
- *Riesgo de prima*: Las primas cobradas son insuficientes para cubrir la siniestralidad. Formula: alpha * primas_retenidas * sigma * factor_diversificacion, donde alpha = 3.0 (factor de confianza al 99.5%) y sigma es el coeficiente de variacion historico de la siniestralidad.
- *Riesgo de reserva*: Las reservas de siniestros pendientes son insuficientes.

**Riesgo de inversion** (`RCSInversion`). Tres subriesgos:
- *Mercado*: Caida en el valor de activos. Shocks calibrados por tipo: acciones -35%, bonos gubernamentales -5% (ajustado por duracion), bonos corporativos -15%, inmuebles -25%.
- *Credito*: Incumplimiento de emisores. Shocks que van desde 0.2% para AAA hasta 50% para calificacion C.
- *Concentracion*: Exposicion excesiva a un solo emisor.

La agregacion final la realiza el `AgregadorRCS` usando una **matriz de correlacion** que evita sumar los riesgos linealmente (lo cual sobreestimaria el capital necesario):

|  | Vida | Danos | Inversion |
|---|---|---|---|
| **Vida** | 1.00 | 0.00 | 0.25 |
| **Danos** | 0.00 | 1.00 | 0.25 |
| **Inversion** | 0.25 | 0.25 | 1.00 |

La correlacion vida-danos es 0.00 (riesgos independientes: que alguien muera no esta correlacionado con que un coche choque). La correlacion vida-inversion y danos-inversion es 0.25 (las inversiones respaldan las reservas de ambos ramos; una caida de mercado afecta la capacidad de cumplir con ambos tipos de obligaciones). La formula de agregacion es la raiz cuadrada de la forma cuadratica: RCS_total = sqrt(Rv^2 + Rd^2 + Ri^2 + 2*rho_vi*Rv*Ri + 2*rho_di*Rd*Ri), donde Rv, Rd, Ri son los RCS por categoria y rho los coeficientes de correlacion.

Como ejemplo concreto, usando los valores que aparecen en el schema del `ResultadoRCS`: RCS vida $28M, RCS danos $30M, RCS inversion $35M. La suma lineal daria $93M, pero la agregacion con correlaciones da $75M -- un ahorro de capital de $18M que refleja el beneficio de la diversificacion. La aseguradora con capital de $100M tendria un ratio de solvencia de 0.75 y cumpliria con la regulacion.

### Circular S-11.4: Reservas Tecnicas

La Circular S-11.4 de la CNSF define como deben calcularse las reservas tecnicas. La suite implementa dos reservas clave:

**Reserva Matematica (RM)** para seguros de vida de largo plazo. La `CalculadoraRM` usa el metodo prospectivo: RM = VP(Beneficios Futuros) - VP(Primas Futuras). Para un asegurado de 45 anos que contrato a los 40 un seguro de vida con prima anual de $25,000 y suma asegurada de $1,000,000, la RM refleja que ya se han acumulado 5 anos de exposicion sin siniestro, por lo que las obligaciones futuras netas de primas por cobrar son positivas. La reserva crece con el tiempo hasta alcanzar la suma asegurada (en el caso del ordinario) o cero al vencimiento (en el caso del temporal).

**Reserva de Riesgos en Curso (RRC)** para seguros de corto plazo. Cubre la porcion de prima no devengada mas un ajuste por insuficiencia si la siniestralidad esperada excede lo previsto.

Ambos modulos incluyen un validador de suficiencia que verifica si las reservas constituidas son adecuadas frente a las obligaciones estimadas.

### Validaciones SAT

Ningun otro paquete actuarial de codigo abierto implementa las reglas fiscales mexicanas para seguros. La suite incluye un `ValidadorPrimasDeducibles` que determina, dado un tipo de seguro y el regimen fiscal del contribuyente, que porcion de la prima es deducible para ISR:

- **Gastos Medicos Mayores (personas fisicas)**: 100% deducible sin limite (LISR Art. 151, fraccion I).
- **Seguros de vida (personas fisicas)**: No deducibles.
- **Planes de pensiones (personas fisicas)**: Deducibles hasta 5 UMAs anuales (LISR Art. 151, fraccion V).
- **Seguros de personal (personas morales)**: 100% deducibles -- GMM, vida e invalidez de empleados (LISR Art. 25, fraccion VI).
- **Seguros sobre bienes (personas morales)**: 100% deducibles como gastos estrictamente indispensables.

El validador recibe la UMA anual vigente como parametro, calcula limites en pesos, y devuelve un `ResultadoDeducibilidadPrima` con el monto deducible, porcentaje y fundamento legal exacto. Esto automatiza una consulta que tipicamente requiere que un contador revise manualmente la LISR.

### Reportes CNSF

El modulo de reportes estructura los datos trimestrales que las aseguradoras presentan a la CNSF. Cuatro generadores especializados producen reportes de suscripcion (primas emitidas, devengadas y canceladas por ramo), siniestros (ocurridos, pagados y pendientes), inversiones (portafolio por tipo de activo) y RCS (desglose completo por tipo de riesgo).

El modelo `MetadatosReporte` valida que la fecha de presentacion sea posterior al trimestre reportado (no puedes presentar el reporte del Q1 antes de que termine marzo), y los `DatosSuscripcionRamo` verifican coherencia entre primas emitidas, devengadas y canceladas. Son validaciones que en Excel dependen de que alguien haya puesto una formula condicional en la celda correcta; aqui son reglas de negocio inamovibles.

Estos modulos regulatorios se benefician mutuamente de todo lo construido en las fases anteriores. La tarificacion alimenta los calculos de RCS vida (sumas aseguradas, reservas matematicas). Las reservas avanzadas alimentan el RCS danos (reservas de siniestros). Y los tres convergen en el reporte CNSF. Es la misma integracion que motivo construir una suite en lugar de scripts sueltos. Para una vision complementaria de como funciona la modelacion de mortalidad desde datos crudos, [SIMA](/proyectos-y-analisis/sima) recorre ese camino con el metodo Lee-Carter sobre datos del INEGI.

## Decisiones de Ingenieria

La suite tiene 34 modulos de produccion distribuidos en 7 subpaquetes (`core`, `actuarial`, `products`, `reinsurance`, `reservas`, `regulatorio`, `reportes`) y 16 archivos de prueba con 307 tests y 87% de cobertura. Son aproximadamente 6,500 lineas de codigo de produccion y 5,500 de pruebas.

**Dependencias unidireccionales.** El flujo de dependencias sigue una sola direccion: `core` no importa de nadie; `products`, `reinsurance`, `reservas` y `regulatorio` importan de `core`; `reportes` importa de `regulatorio`. No hay ciclos. Esto permite que cualquier modulo se pruebe de forma aislada.

**Mas de 30 modelos Pydantic** con `json_schema_extra` que incluyen ejemplos concretos. Cada modelo funciona como documentacion ejecutable: los ejemplos en el schema son instancias validas que se pueden copiar directamente en un test o en una sesion interactiva.

**Precision Decimal** en toda la cadena. Desde el `qx` de la tabla de mortalidad hasta el resultado final del RCS, cada calculo usa `Decimal` en lugar de `float`. La configuracion de producto especifica tasas como `Decimal("0.055")`, no como `0.055`. Las primas se redondean a centavos con `quantize(Decimal("0.01"))`.

**CI con GitHub Actions.** La suite se prueba automaticamente contra Python 3.11 y 3.12. El pipeline ejecuta `ruff` para linting (line-length 100, target-version py311), `mypy` con el plugin de Pydantic para verificacion de tipos, y `pytest` con medicion de cobertura. La configuracion de `mypy` activa `disallow_untyped_defs` y `warn_return_any` -- decisiones que duelen al momento de escribir el codigo pero que pagan dividendos cuando la base crece.

**Dashboard Streamlit.** Tres paginas interactivas con Plotly: calculadora de productos de vida (comparacion entre temporal, ordinario y dotal con analisis de sensibilidad), monitor de cumplimiento regulatorio (calculadoras de RCS y validaciones SAT), y analisis de reservas tecnicas (triangulos de desarrollo, proyecciones y comparacion de metodos). El layout `wide` aprovecha el espacio para metricas y columnas lado a lado.

## Lo que Aprendi

**Primera** leccion: Pydantic como guardia de dominio es cualitativamente diferente de las pruebas unitarias. Un `model_validator` que verifica que los recargos totales no excedan el 100% captura una clase entera de errores en el punto de entrada, antes de que los datos toquen una formula. Con pruebas unitarias, necesitas imaginar y escribir cada caso invalido. Con Pydantic, defines la regla una vez y el modelo rechaza todo lo que no cumpla, incluyendo casos que nunca imaginaste. Los mensajes de error son para el usuario, no para el desarrollador -- "Recargos totales (115%) superan el 100%" comunica el problema de forma inmediata. Esto es especialmente valioso en software actuarial, donde el usuario es un actuario que entiende el dominio pero no necesariamente el stack tecnologico.

**Segunda** leccion: la matriz de correlacion del RCS esconde juicio regulatorio. La formula de agregacion es algebra vectorial sencilla -- una raiz cuadrada de forma cuadratica. Lo dificil no es implementar la formula sino entender **por que** la CNSF eligio esas correlaciones especificas: 0.00 entre vida y danos, 0.25 entre vida e inversion, 0.25 entre danos e inversion. El 0.00 entre vida y danos refleja la independencia estadistica entre mortalidad y siniestros de automoviles. El 0.25 con inversion refleja que una crisis financiera afecta la capacidad de pago de ambos tipos de obligaciones a traves de la cartera de inversiones. Estos numeros codifican la vision del regulador sobre como interactuan los riesgos en el mercado mexicano. Implementar la formula sin entender la logica detras de los parametros es mecanografia, no ingenieria actuarial.

**Tercera** leccion: la especificidad regulatoria mexicana es la parte dificil. Chain Ladder es Chain Ladder en Mexico, en Francia o en Japon. La formula de una anualidad anticipada es identica en cualquier jurisdiccion. Lo que hace que esta suite sea util **especificamente para Mexico** son los modulos que no existen en ningun otro paquete: la EMSSA-09 como tabla base de tarificacion, la Circular S-11.4 para reservas tecnicas, las reglas de deducibilidad del articulo 151 de la LISR, los formatos de reporte CNSF con sus validaciones de fechas y trimestres. Esos modulos fueron los que requirieron mas horas de investigacion en documentos de la CNSF, circulares y textos de ley, con las menores referencias de implementacion disponibles.

## Cierre

La Suite Actuarial Mexicana demuestra que es posible cubrir el ciclo operativo completo de una aseguradora -- desde la mortalidad cruda hasta el reporte regulatorio -- en una sola libreria de Python con validacion rigurosa y precision decimal, sin depender de software propietario.

**Repositorio**: [github.com/GonorAndres/suite-actuarial](https://github.com/GonorAndres/suite-actuarial)
