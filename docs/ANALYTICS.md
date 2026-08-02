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
