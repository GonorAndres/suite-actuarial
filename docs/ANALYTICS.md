# Analítica de producto — contrato y configuración

La interfaz pública y la API usan un contrato mínimo de analítica. El backend envía a
PostHog sólo métricas de salud de las solicitudes cuando el despliegue tiene configurada
una clave de proyecto. Sin esa variable, no se envía nada.

## Eventos de API

El backend emite `api_request` de forma asíncrona. Sus propiedades permitidas son:

| Propiedad | Significado |
| --- | --- |
| `api_route` | Ruta sin query string |
| `http_method` | Método HTTP |
| `status_code` | Código de respuesta |
| `duration_ms` | Duración redondeada |
| `outcome` | `success`, `client_error` o `server_error` |

Configura el servicio FastAPI con:

```bash
POSTHOG_PROJECT_API_KEY=phc_...
POSTHOG_HOST=https://us.i.posthog.com
```

`POSTHOG_API_KEY` también se acepta como nombre alternativo. La clave nunca se incluye
en la interfaz ni se registra en logs. El envío usa un identificador anónimo fijo y no
crea perfiles de personas.

Este evento se escribió antes de que ningún despliegue tuviera la variable configurada,
así que no envió nada hasta el 2026-08-02. Desde esa fecha `deploy.yml` la inyecta.

## Eventos del borde

El worker de [`edge/`](../edge/) emite `api_edge_request`. Es un evento distinto, no
una segunda fuente de `api_request`, por dos razones: el origen nunca ve una petición
frenada por límite de tasa ni una servida desde caché, así que las cuentas no
coincidirían; y manteniéndolos separados, la diferencia entre ambos se lee como «el
borde la absorbió» en vez de parecer pérdida de datos.

| Propiedad | Significado |
| --- | --- |
| `api_route` | Ruta normalizada. Los años y las fechas se colapsan a `:num` y `:date`, y cualquier ruta no definida se reporta como `<unmatched>`, para que un escaneo no genere un valor nuevo por sondeo |
| `http_method` | Método HTTP |
| `status_code` | Código de respuesta |
| `duration_ms` | Duración redondeada, medida en el borde |
| `outcome` | `success`, `client_error`, `server_error` o `rate_limited` |
| `cache` | `hit`, `miss` o `bypass` |
| `auth_tier` | `anonymous` o `key` |
| `api_key_label` | Etiqueta del consumidor, sólo cuando presentó clave. Nunca la clave |
| `country` | País que reporta Cloudflare |
| `colo` | Ubicación de Cloudflare que atendió la petición |

`country` y `colo` son nuevos respecto del contrato del backend. Son geografía gruesa:
dicen desde dónde se usa el API, no reconstruyen a quién. Todo lo demás que el contrato
excluye sigue excluido: cuerpos de solicitud, query strings, respuestas, entradas o
resultados actuariales, user agents, direcciones IP y las claves mismas. La IP se usa
sólo como contador del límite de tasa y no sale del borde.

El identificador es fijo (`suite-actuarial-api-edge`) para tráfico anónimo y
`key:<etiqueta>` para quien presenta clave. En ambos casos `$process_person_profile`
va en falso: la analítica dice qué superficies se usan y por qué integración, no
construye un perfil.

Una prueba fija el conjunto exacto de propiedades (`edge/test/telemetry.test.ts`).
Cambiar el contrato exige cambiar esa prueba y esta tabla en el mismo movimiento.

## Eventos de producto previstos

Estos eventos de interfaz siguen siendo el contrato para una futura instrumentación
explícita de navegación:

| Evento | Propiedades permitidas |
| --- | --- |
| `calculator_opened` | `domain`, `model`, `language` |
| `calculation_succeeded` | `domain`, `model`, `language` |
| `calculation_failed` | `domain`, `model`, `language`, categoría de error |
| `result_downloaded` | `domain`, `model`, `format` |
| `language_changed` | idioma de destino |
| `github_clicked` | ruta pública de origen |

No se envían entradas actuariales, cuerpos de solicitud, importes, edades, identificadores
de siniestro, user agents, IPs ni resultados. La analítica explica qué superficies y rutas
se usan; no reconstruye los escenarios de una persona.
