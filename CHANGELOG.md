# Changelog

## Sin publicar — rutas por idioma en el tablero

El inglés deja de ser invisible para los buscadores. Antes había 568 claves
traducidas en paridad exacta y cero URLs indexables: los doce documentos exportados
eran español con `lang="es"`, y el idioma era estado de cliente en `localStorage`.
Ahora cada ruta existe dos veces: el documento español en su URL original (ninguna
cambia) y el inglés bajo `/en/`, con la misma prioridad en el sitemap.

- Dos root layouts por grupos de ruta (`app/(es)/`, `app/(en)/en/`); el HTML
  exportado declara `lang` real y el contenido inglés se prerrenderiza — un
  rastreador sin JavaScript ve inglés en `/en/`, cosa que una prueba fija.
- hreflang recíproco (`es-MX`, `en-US`, `x-default` → español) en las 24 páginas y
  en el sitemap; canónico y `og:locale` por variante.
- JSON-LD localizado: los nodos de sitio (`#website`, `#person`, `#software`)
  comparten `@id` entre árboles; los nodos de página y la divulgación de alcance
  son por idioma, con textos citados literalmente del contenido real.
- El idioma viene de la ruta: `LanguageProvider` recibe `lang` del layout;
  desaparecen `localStorage`, el snippet previo a hidratación y `DocumentLanguage`
  (~45 líneas menos). El conmutador es un enlace real al documento gemelo y
  conserva ruta, query y hash (el estado del workbench sobrevive el cambio).
- Compuertas nuevas en Playwright: 33 pruebas (antes 18) — paridad de claves,
  hreflang recíproco, estado activo del Header bajo `/en/`, navegación contenida
  en cada árbol, y el conmutador con query y hash.

## Sin publicar — borde público del API

El API deja de estar expuesto directamente. `api-suite.gonor.me` pasa a servirse por
un worker de Cloudflare (`edge/`) que proxia a Cloud Run. La dirección no cambia, así
que ningún cliente existente se rompe.

Qué gana el API con esto, y por qué cada pieza tiene que estar delante y no detrás:

- **Límite de tasa**: 120 peticiones/minuto por IP, 1200 con clave. `docs/DEPLOYMENT.md`
  señalaba esta como la capa que faltaba: el techo de gasto era `--max-instances`, y
  todo lo demás sólo reducía la probabilidad de llegar a él. Ahora el abuso se rechaza
  en Cloudflare, donde es gratis, antes de arrancar un contenedor.

  El techo es aproximado y conviene no venderlo como más de lo que es. Medido contra
  el despliegue real: 250 peticiones sobre una conexión reutilizada cortaron cerca de
  la 108, pero 200 sobre 25 conexiones en paralelo no cortaron ninguna. El conteo es
  por máquina del borde. Frena a un raspador ingenuo, no a uno distribuido, y
  `--max-instances` sigue siendo el único límite duro de facturación.
- **CORS público**: terceros pueden llamar desde un navegador. Antes la lista del
  origen nombraba sólo `suite.gonor.me`, así que el API era público de nombre pero no
  utilizable desde ninguna otra aplicación web.
- **Caché del borde** para `/api/info` y `/api/v1/config/*`, que son idénticos para
  cualquiera y cambian sólo con un despliegue. Ningún cálculo se cachea nunca: llevan
  los supuestos de quien llama.
- **Claves de API opcionales**: sin clave se atiende igual, con el límite bajo. Una
  clave sólo sube el límite y etiqueta la analítica. KV guarda el SHA-256, nunca la
  clave, y las cabeceras de autorización se eliminan antes de llamar al origen.

### Analítica

- Nuevo evento `api_edge_request` desde el borde, con `cache`, `auth_tier`, `country` y
  `colo` además del contrato del backend. Es un evento distinto de `api_request`
  porque el origen nunca ve una petición frenada por límite de tasa ni servida desde
  caché. Contrato completo en `docs/ANALYTICS.md`.
- **`api_request` empieza a enviarse de verdad.** El código de `api/telemetry.py`
  existía desde que se escribió, pero `deploy.yml` nunca definió
  `POSTHOG_PROJECT_API_KEY`, así que no había enviado un solo evento. Ahora la inyecta.

### Operación

- Producción pasa a definir `SUITE_PROXY_SHARED_SECRET`, que hasta ahora sólo usaba
  dev. Reactivar la URL `run.app` del servicio —necesaria para que el worker tenga a
  dónde llamar— crearía si no un rodeo sin límite de tasa alrededor del borde.
- El worker se adjunta por **ruta**, no por dominio personalizado: `api-suite.gonor.me`
  ya tiene CNAME al mapeo de dominio de Cloud Run, y tomarlo con un dominio
  personalizado exigiría borrar el registro y dejar el API caído. Borrar la ruta es la
  reversión.
- Nueva compuerta en CI: `typecheck` y pruebas del worker, ejecutadas dentro de
  workerd.

## 2.2.0 (2026-08-02) — remediación de la auditoría actuarial (`docs/AUDIT.md`)

Las seis fases de la auditoría están cerradas: los diez hallazgos Clase A corregidos,
cada uno con una prueba cuyo valor esperado procede de una fuente externa, una
identidad actuarial o un cálculo a mano. Los techos Clase B siguen vigentes y ahora
tienen inventario por modelo, con fuente, vigencia y ruta de sustitución.

### Breaking — el campo `sexo` pasa a palabras completas

El proyecto tenía dos codificaciones de sexo incompatibles y el mismo carácter
significaba cosas opuestas según el endpoint:

- `core/models/common.py`, y con él `vida/`, `pensiones/`, `/api/v1/pricing/*` y
  `/api/v1/pensiones/*`, usaba `H` (hombre) / `M` (mujer).
- `salud/gmm.py`, `salud/accidentes.py` y `/api/v1/salud/*` usaban `M` (masculino) /
  `F` (femenino).

Es decir: `"sexo": "M"` significaba **hombre** en `/api/v1/salud/gmm/calcular` y
**mujer** en `/api/v1/pricing/temporal`. Un cliente que reutilizara el mismo valor
entre dos realms cambiaba de sexo al asegurado sin ningún error, y con él la tabla de
mortalidad que fija la prima.

La convención única es ahora la palabra completa: `Sexo.MASCULINO = "masculino"` y
`Sexo.FEMENINO = "femenino"`, en el paquete, la API, el dashboard, la app de Streamlit
y los ejemplos. Los **nombres** de los miembros del enum también cambian
(`Sexo.HOMBRE`/`Sexo.MUJER` dejan de existir), así que el código Python que los
importaba rompe en el import, no en silencio.

- **Las tres iniciales `"H"`, `"M"` y `"F"` son ahora inválidas en todos los endpoints
  con campo `sexo`** (`/api/v1/pricing/{temporal,ordinario,dotal,compare}`,
  `/api/v1/pricing/dotal/lab`, `/api/v1/salud/{gmm,accidentes}/calcular`,
  `/api/v1/pensiones/{ley97,renta-vitalicia}/calcular` y el parámetro de query de
  `/api/v1/pensiones/conmutacion/tabla`). Devuelven 422 con el conjunto válido en el
  detalle (`Input should be 'masculino' or 'femenino'`). La ruptura es deliberada y
  ruidosa: ninguna letra se reinterpreta en silencio, porque cualquier traducción
  automática de `"M"` habría acertado en un realm y errado en el otro. Hay una prueba
  de regresión por router que lo fija.
- El campo `sexo` de las respuestas (`Ley97Response`, `RentaVitaliciaResponse`,
  `ConmutacionResponse`, el bloque `asegurado` de GMM) devuelve las mismas palabras.
- OpenAPI enumera los dos valores en vez de publicar un `pattern` de una letra;
  `frontend/src/lib/types.ts` exporta el tipo `Sexo = "masculino" | "femenino"`.
- El CSV de EMSSA-09 (`src/suite_actuarial/data/mortality_tables/emssa_09.csv`) **no
  cambia**: es un
  insumo controlado y conserva la columna `sexo` con las iniciales publicadas `H`/`M`.
  La traducción ocurre una sola vez, en `TablaMortalidad.desde_csv`. La tabla en
  memoria y todas las consultas públicas hablan ya la convención nueva, y construir
  `TablaMortalidad` con un DataFrame en iniciales falla.
- Las etiquetas visibles siguen siendo "Hombre"/"Mujer" y "Masculino"/"Femenino"
  según la pantalla; lo que cambió es el valor transmitido.

### Breaking — la Reserva Matemática se reescribió: el cálculo no era una reserva

`regulatorio/reservas_tecnicas/reserva_matematica.py` usaba la probabilidad de
supervivencia de **un** año como si cubriera todo el plazo remanente, consultaba
siempre mortalidad masculina sin mirar el sexo del asegurado, fijaba ω = 85 y fin de
pago de primas a los 65 sin fuente, y caía en una ley de supervivencia sin cita,
`exp(-0.00008·x²)`, cuando no se le pasaba tabla. El módulo se reescribió como
reserva prospectiva de primas netas, ₜV = SA·A_{x+t:n−t} − P·ä_{x+t:m−t}, construida
sobre la maquinaria auditada de `actuarial/pricing/vida_pricing.py`. Todas las
cifras de RM cambian.

- **`ConfiguracionRM` (cambio incompatible).** `sexo` y `plazo_seguro_anios` son
  ahora obligatorios; `plazo_pago_anios` toma por omisión el plazo de cobertura;
  `prima_nivelada_anual` es opcional y, si se omite, la prima neta se determina por
  el principio de equivalencia a la edad de contratación.
- **`CalculadoraRM` exige tabla de mortalidad.** No hay ley de supervivencia de
  respaldo: una reserva calculada con una curva sin fuente no es una reserva. La
  edad terminal ω se lee de la tabla cargada y se aplica la convención auditada
  q_ω = 1 (hallazgo A7).
- **`ResultadoRM` publica la reserva con signo.** Una reserva negativa significa que
  las primas futuras valen más que los beneficios futuros; ocultarlo rompía la
  recursión de Fackler. El importe a constituir en balance va aparte en
  `reserva_a_constituir`, y el resultado trae además `prima_neta_anual`,
  `probabilidad_supervivencia_plazo` (ahora ₙp_x, no 1−qx) y `disclaimer`.
- El módulo dejó de declarar conformidad con la Circular S-11.4: declara estar
  orientado a ella, sobre tabla ilustrativa y prima neta, sin gastos ni caducidad ni
  margen de riesgo. Avisa con `ExperimentalModelWarning` al construirse. Las pruebas
  fijan la identidad retrospectiva/prospectiva (Fackler) en cada duración y un valor
  calculado a mano, y demuestran que la verificación falla ante el defecto que se
  eliminó.

### Corregido — deducibilidad Art. 151 LISR y cobertura de perfiles regulatorios

- El tope global de deducciones personales del último párrafo del Art. 151 de la
  LISR ya se aplica a las primas de gastos médicos mayores de persona física; antes
  se devolvían 100% deducibles "sin límite". El tope es el menor entre cinco veces
  el valor anual de la UMA y el 15% del total de los ingresos del contribuyente;
  ambas cifras salen del perfil regulatorio del año y de un nuevo insumo opcional
  `ingresos_totales_anuales`. Sin ese insumo solo puede aplicarse la rama de las
  cinco UMA y la respuesta lo dice (`tope_global: "parcial_sin_ingresos"`, estado
  `indeterminate`) en lugar de devolver un 100% en silencio. Fuente: Ley del ISR,
  texto vigente consolidado por la Cámara de Diputados, última reforma DOF
  01-04-2024, consultada el 2026-08-02.
- La cita de la fracción de las primas de GMM pasa de la I a la **VI**. La fracción
  I son honorarios médicos y gastos hospitalarios, no primas.
- El tope propio de la fracción V (planes personales de retiro) se calculaba al 15%
  de los ingresos; el estatuto dice **10%** de los ingresos acumulables, sin exceder
  cinco UMA anuales. La fracción V está además excluida expresamente del tope
  global, y el resultado ahora lo declara.
- Agotada la cobertura de perfiles regulatorios empaquetados (2024-02-01 a
  2027-01-31), los endpoints regulatorios devolvían 500 con traceback. Ahora el
  cargador lanza `ConfiguracionNoDisponibleError` con el rango cubierto en el
  mensaje, `/api/v1/regulatory/*` responde 503 y `/api/v1/config/fecha/{fecha}`
  responde 422. No se inventan parámetros del año siguiente ni se reutiliza en
  silencio el último perfil publicado.

### Corregido — un solo camino de carga, verificado, para la tabla de mortalidad

- `TablaMortalidad.cargar_emssa09()` tenía dos caminos de carga. El de respaldo
  buscaba el CSV por rutas relativas al directorio de trabajo (incluida una copia
  duplicada en la raíz del repositorio), lo cargaba sin metadatos y sin modo
  estricto, y la tabla sintética terminaba reportando `validation_tier: supported`.
  Ahora hay un solo camino, siempre estricto y siempre con metadatos: el paquete de
  datos instalado. Si el archivo falta, la instalación está rota y se reporta como
  tal en vez de degradar la carga.
- El `content_hash` declarado en `metadata.json` se sobrescribía con un sha256
  recalculado en cada carga, de modo que siempre coincidía consigo mismo y no
  verificaba nada. Ahora se calcula el sha256 del CSV y se compara contra el
  declarado; si difieren, la carga se detiene con ambos digests en el mensaje.
- Eliminada la copia duplicada `data/mortality_tables/` de la raíz del repositorio;
  la única copia de la tabla viaja dentro del paquete
  (`src/suite_actuarial/data/mortality_tables/`), junto con su README.
- CLI: el mensaje de error de `seguros demo` apuntaba a la ruta raíz eliminada
  (ahora indica reinstalar el paquete) y `seguros api` sugería
  `pip install mexican-insurance[api]`, nombre de paquete inexistente (ahora
  `pip install 'suite-actuarial[api]'`).

### Añadido — daños y salud declaran su alcance donde se lee la cifra

- `GMM`, `AccidentesEnfermedades`, `SeguroAuto`, `SeguroIncendio` y `SeguroRC`
  emiten `ExperimentalModelWarning` al construirse, y las respuestas de
  `/api/v1/salud/{gmm,accidentes}/calcular` y
  `/api/v1/danos/{auto,incendio,rc}/calcular` llevan `disclaimer` y
  `validation_tier` (cambio aditivo del contrato; `frontend/src/lib/types.ts` los
  declara opcionales). Antes las constantes `DISCLAIMER` de `salud/gmm.py` y
  `danos/tablas_amis.py` existían sin que nadie las importara, e incendio, RC y
  accidentes no tenían aviso alguno.
- Dos avisos se corrigieron por exactitud: `danos/tablas_amis.py` ya no presenta sus
  tasas como "la tarifa de referencia de mercado" ni remite a tablas publicadas por
  la AMIS que el repositorio no puede evidenciar; `salud/gmm.py` añade que la
  siniestralidad esperada se deriva de la propia prima (`prima/(1+margen)`, un
  cálculo circular) y que el sexo no altera el precio.
- Streamlit: las pestañas de Daños, Salud y Reaseguro muestran el límite junto al
  resultado; en Pensiones, "Recomendación: X" pasa a "Modalidad con mayor pensión
  mensual inicial: X" con la salvedad de que el modelo no recomienda una modalidad;
  en Salud, el tope de coaseguro del simulador (10% de la suma asegurada) se declara
  en la página como supuesto y se calcula en `Decimal` exacto.

### Corregido — el dashboard enviaba y mostraba unidades equivocadas en reaseguro

- **Cuota parte estaba mal por un factor de 100 en el dashboard.** La API espera
  `porcentaje_cesion` y `comision_reaseguro` en puntos porcentuales (0–100) y divide
  entre 100 internamente; `frontend/src/app/reaseguro/page.tsx` volvía a dividir
  entre 100 antes de enviar. Un usuario que pedía 40% de cesión obtenía la economía
  de 0.4%: monto cedido $20,000 en lugar de $2,000,000 sobre una prima de $5M. La
  celda "Ratio de cesión: 40.00%" enmascaraba el error porque el formateador
  multiplicaba por 100 la respuesta (que ya viene en por ciento). Se elimina la doble
  división y `ratio_cesion` se formatea como el valor porcentual que ya es.
- La tasa de prima del contrato XL se etiqueta ahora "(%)" con default 5 (antes un
  campo sin unidad con default 0.05, que el backend leía como 0.05% y subestimaba
  la prima de reinstalación por el mismo factor de 100).
- El dashboard muestra `disclaimer` y `validation_tier` en daños y salud (auto,
  incendio, RC, GMM, accidentes), como ya hacía vida; la deducibilidad envía
  `ingresos_totales_anuales` y muestra `tope_global`/`nota_tope_global` (la rama del
  15% del Art. 151 era inalcanzable desde la UI); las tasas al millar (incendio, RC)
  se muestran como "0.80 ‰" y no "80.00%"; las claves crudas de la API
  (`sedan_compacto`, `tope_coaseguro: null`, `danos_materiales`…) pasan por un mapa
  de etiquetas bilingüe (`frontend/src/lib/field-display.ts`); los errores de la API
  se muestran como mensaje legible y no como el JSON crudo; y el proveedor de idioma
  ya no produce un error de hidratación cuando el idioma persistido no es español.
- `danos/auto.py`: el mensaje de deducible inválido nombra las opciones como
  porcentajes ("3%, 5%, 10%, 15%, 20%") en lugar de filtrar el `repr` de `Decimal`;
  el formulario del dashboard ofrece las cinco opciones válidas en un selector.
- `frontend/src/app/api-docs/page.tsx` se cotejó endpoint por endpoint contra
  `openapi.json`: se añaden `/pricing/dotal/lab`, `/config/validate` y
  `/config/fecha/{fecha}`; se retira la afirmación falsa de que auto usa "tablas de
  referencia AMIS"; la descripción de Ley 97 ya no dice que "recomienda la mejor
  opción"; y la prosa en español recupera los acentos.

### Cambiado — la prosa en español del dashboard, el README y Streamlit

- Reescritura de la copy en español de todas las superficies que lee un visitante:
  portada, diccionario i18n, guías de dominio y de workbench, ejemplo guiado,
  biblioteca, evidencia, metadatos de página, descripciones de `api-docs`, README y
  `streamlit_app/`. Se retiran los paréntesis con raya (`—`) de la prosa, se unifica
  el tratamiento en segunda persona (`tú`) que antes convivía con `usted`, y se
  bajan las afirmaciones de venta: `100% open source ... Auditable, extensible,
  gratuito` pasa a describir lo que da la licencia MIT. Ningún cambio de cifras.
- Se corrige una afirmación que contradecía la divulgación del propio módulo:
  `streamlit_app/Home.py` anunciaba `tarificación AMIS` para auto y
  `pages/2_Danos.py` titulaba `Seguro de auto (AMIS)`, mientras el caption de esa
  misma página declara que las tasas *no proceden de la AMIS*. Ahora dicen
  `tasas ilustrativas`. Es el mismo texto falso que ya se había retirado de
  `api-docs`.

### Corregido — el conmutador de vista se desplazaba sobre el texto al hacer scroll

- `DomainWorkspace.tsx` aplicaba su transformación de ocultamiento en cuanto se
  bajaba de 24 px, sin comprobar si la barra había llegado a su desplazamiento
  sticky. Mientras seguía en el flujo normal, la transformación no la ocultaba: la
  arrastraba 162 px hacia arriba **encima del párrafo anterior**, tapándolo a media
  frase, y dejaba un hueco donde estaba la barra. Ahora sólo se oculta cuando está
  fijada bajo la cabecera, medido con la cadena de `offsetTop` (inmune a la propia
  transformación del elemento, que contaminaría un `getBoundingClientRect`).
- La traslación era además 48 px corta: `calc(100% + 1rem)` no contaba el
  desplazamiento sticky de 64 px, así que al ocultarse quedaba una franja de la
  barra fija arriba con una línea de texto cortada. Pasa a `calc(100% + 5rem)`.
- Prueba de regresión en `frontend/tests/public-exposition.spec.ts`, verificada en
  rojo revirtiendo la corrección antes de darla por buena.

### Añadido — los ejemplos y los benchmarks publicados entran a la suite

- Los ejemplos autoverificables de `examples/casos/` y `examples/labs/` se ejecutan
  ahora dentro de la suite (`tests/unit/test_examples.py`): cada script corre con
  `runpy` y sus 43 aserciones de identidad actuarial fallan la suite si dejan de
  cumplirse. Hasta ahora ningún gate los ejecutaba, aunque el README de los casos
  promete que "si una falla, el script truena". Una guarda exige que cada ejemplo
  conserve al menos una sentencia `assert`.
- `tests/unit/test_validation_benchmarks.py` fija los números publicados en
  `docs/VALIDATION.md`: los spot checks de qx, las cuatro propiedades declaradas de
  la tabla, los valores de conmutación a i = 5.5%, la identidad Ax + d·äx = 1 y
  Nx = Σ Dx, Mx = Σ Cx. Todos los valores publicados coincidieron con el cálculo;
  ninguno se modificó.

### Añadido — Bonus-Malus y modelo colectivo declaran su alcance

Eran las dos únicas respuestas de daños que seguían sin `disclaimer` ni
`validation_tier`, así que sus dos pestañas del dashboard no podían divulgar nada
aunque el resto del realm ya lo hacía.

- `danos/tarifas.py` expone `DISCLAIMER` y `VALIDATION_TIER`, y
  `CalculadoraBonusMalus` emite `ExperimentalModelWarning` al construirse. La
  escala se describía en el código como «escala estándar mexicana» y «escala
  típica mexicana» sin fuente alguna: los nueve niveles, sus factores y las
  reglas de transición se construyeron para el laboratorio. El aviso lo dice, y
  añade el límite que la cifra no muestra — la escala no está calibrada. Una
  prueba lo hace visible: con un siniestro cada dos periodos el asegurado deriva
  al recargo máximo y se queda ahí.
- `danos/frecuencia_severidad.py` expone `DISCLAIMER` y `VALIDATION_TIER`, y
  `ModeloColectivo` emite el mismo aviso. Aquí el método es estándar; lo que no
  está respaldado son los parámetros, que fija quien llama sin ajustarlos a dato
  alguno. El aviso nombra además los supuestos invisibles en el resultado:
  independencia entre N y X, ausencia de deducible, límite, reaseguro, inflación
  y descuento, parámetros tratados como conocidos, y el error de muestreo Monte
  Carlo que la respuesta no reporta.
- `BonusMalusResponse` y `FrecuenciaSeveridadResponse` llevan los dos campos
  nuevos (cambio aditivo del contrato), con prueba por realm; `types.ts` los
  declara y los dos paneles del dashboard los renderizan con `AvisoModelo`.
- Dos renglones nuevos en el [inventario Clase B](docs/AUDIT.md#inventario-clase-b-fase-5).

Con esto, las cinco respuestas de daños divulgan su alcance.

### Corregido — `POST /danos/frecuencia-severidad` devolvía 500 con traceback

Las distribuciones se construyen indexando el diccionario recibido
(`p["lambda_"]`), así que `params_frecuencia: {"lambda": 5.0}` —o un `pareto` sin
`scale`— reventaba como `KeyError` dentro del modelo y salía como error interno.
El contrato dice justo lo contrario: preservar el error útil y no exponer el
traceback. La UI no podía provocarlo porque siempre envía `lambda_`; un cliente
del API sí.

- `PARAMS_FRECUENCIA` y `PARAMS_SEVERIDAD` declaran los nombres exactos que exige
  cada distribución. Son la única fuente de verdad: `ModeloColectivo` valida
  contra ellos al construir (`ValueError` en vez de `KeyError`, para quien use el
  paquete) y el borde HTTP los nombra en un **422** con el juego válido.
- Asimetría deliberada, con prueba que la fija: el nombre de la distribución
  sigue validándose en el dominio y devolviendo 400. Sin juego de parámetros
  contra el cual comparar, el borde no puede decir nada útil; `ModeloColectivo`
  sí, y lista sus opciones.

### Corregido — afirmaciones ya retiradas que sobrevivían en los docstrings

El mismo texto falso que se quitó de `api-docs` y de Streamlit seguía en el
backend, y desde ahí volvía a salir por `openapi.json`.

- `routers/danos.py` decía que la cotización de auto usa «AMIS reference
  tables». No las usa: las tasas y factores reproducen la estructura de una
  tarifa, no los valores de ninguna, y no proceden de la AMIS.
- `routers/pensiones.py` decía que Ley 97 «recommends the better option». No
  recomienda: el campo `recomendacion` nombra la modalidad con el primer pago
  mensual más alto, sin ponderar que la renta vitalicia está garantizada de por
  vida mientras el retiro programado se recalcula cada año y puede agotarse.
- `api-docs` describía la escala BMS como «escala BMS mexicana»; ahora dice
  ilustrativa, y sus dos respuestas de ejemplo incluyen los campos nuevos.

### Corregido — documentación que describía métodos ya corregidos

- `docs/portfolio/blog-{es,en}.md` presentaba la Reserva Matemática bajo la
  Circular S-11.4 como si fuera un cálculo conforme, y con la fórmula anterior.
  Ahora declara el método prospectivo de primas netas y dice explícitamente qué
  le falta para ser el cálculo institucional.
- Los mismos dos archivos afirmaban que los GMM de personas físicas son «100%
  deducibles sin límite (Art. 151, fracción I)». Es la afirmación que cerró la
  auditoría: es la fracción **VI** y está sujeta al tope global del último
  párrafo. También precisan la fracción V (menor entre 10% de ingresos
  acumulables y cinco UMA, excluida del tope global) y actualizan el conteo de
  pruebas (985 → 1,380).
- `docs/VALIDATION.md` §6 listaba 6 de los 16 módulos con `DISCLAIMER`; ahora
  están todos, agrupados por dominio y con enlace al inventario Clase B. Se
  retiraron los rótulos `qx_H`/`qx_M`, que dejaron de existir con la migración
  de `sexo` a palabras completas.
- `docs/knowledge/{technical,intuitive}.tex` publicaban la fórmula vieja de la RM
  y su ley de supervivencia `exp(-k·x²)`, ambas retiradas del código.

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

### Compuertas de verificación reparadas

La compuerta de tipos llevaba tiempo sin comprobar nada: los stubs de numpy usan la
sentencia `type` de PEP 695 y mypy, configurado en `python_version = "3.11"`, abortaba
al parsearlos antes de leer un solo archivo del proyecto. En CI el paso además estaba
marcado `continue-on-error`, así que el fallo no se veía. `ruff format --check` no
corría en CI en absoluto, y `examples/` y `streamlit_app/` quedaban fuera de toda
comprobación. Detalle en [`AGENTS.md`](AGENTS.md#verification).

- **Corregido, defecto real que encontró la compuerta al volver a correr.**
  `streamlit_app/pages/6_Regulatorio.py` construía `TablaMortalidad()` sin argumentos,
  cuando `nombre` y `datos` son obligatorios: la pestaña de reserva matemática lanzaba
  `TypeError`. Ahora usa `TablaMortalidad.cargar_emssa09()`, igual que el resto de la
  app. El mismo error aparecía en el bloque de código de ejemplo que la página muestra
  al lector.
- **Nuevo `py.typed` (PEP 561).** El paquete publica sus anotaciones; antes cualquier
  consumidor externo —incluidos `examples/` y `streamlit_app/`— lo veía sin tipos.
- Las cuatro compuertas cubren ahora `src/`, `tests/`, `examples/` y `streamlit_app/`,
  y corren en CI en **todas** las ramas, no solo en `main` y `develop`. `pytest` corre
  en CI con `SUITE_REQUIRE_API=1`.
- `openpyxl` pasa a `[dev]`. Sin él, las dos pruebas de exportación a Excel de
  `test_reportes.py` se saltaban en silencio, en local y en CI.

### Cambios menores de contrato

Ninguno altera un resultado actuarial; se listan porque cambian una firma o un tipo.

- `sum()` sobre agregados de `Decimal` lleva semilla `Decimal("0")` en reportes,
  credibilidad, retenciones y suficiencia. Sobre una colección vacía devuelven
  `Decimal("0")` y no el `int` `0`.
- `CalculadoraRetencionesISR.calcular_retencion_masiva` indexa las claves obligatorias
  (`tipo_seguro`, `monto_pago`, `monto_gravable`) en vez de usar `.get()`. Una clave
  ausente ahora da `KeyError` en el sitio correcto, en lugar de propagar `None`.
- `CurvaRendimiento` acepta `Sequence[float]` en `plazos`: los importadores desde CSV y
  DataFrame ya construían plazos fraccionarios, que `tasa_spot` interpola.
- `RCSInversion.obtener_shocks_aplicados` declara `dict[str, Decimal | str]`: siempre
  devolvió la calificación como texto.
- `VidaOrdinario.plazo_pago` sigue siendo `int | None`; la invariante "es `None` si y
  solo si la prima es vitalicia" se hace explícita en `_plazo_pago_limitado`.

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
