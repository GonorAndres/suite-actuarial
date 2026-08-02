# Handoff — suite_actuarial public foundation

## Estado actual

- La portada presenta el laboratorio, la biblioteca y el alcance antes de pedir datos.
- Los siete dominios tienen dos vistas: `Caso explicado` y `Workbench`.
- Cada Workbench explica qué calcula, para qué sirve y cuál es su límite antes del formulario.
- El encabezado global y los tabs de dominio se ocultan al bajar y reaparecen con un desplazamiento corto hacia arriba.
- `/evidencia` empieza con una lectura sencilla y deja el estado técnico por dominio dentro de un desplegable.
- FastAPI puede servir la exportación estática y responder los POST en el mismo puerto.
- El backend emite `api_request` a PostHog sólo cuando se configura `POSTHOG_PROJECT_API_KEY` o `POSTHOG_API_KEY`.

## Verificación

Desde `frontend/`:

```bash
npm run lint
npm run build
npm run test:e2e
```

Desde la raíz:

```bash
SUITE_REQUIRE_API=1 .venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src/ tests/ examples/ streamlit_app/
.venv/bin/python -m ruff format --check src/ tests/ examples/ streamlit_app/
.venv/bin/python -m mypy src/ tests/ examples/ streamlit_app/
```

## Próximas sesiones

1. Configurar las variables de PostHog en el servicio real y confirmar en el proyecto que sólo llegan `api_request` y sus cinco propiedades permitidas.
2. Añadir eventos de producto en el frontend (`calculator_opened`, `calculation_succeeded`, `calculation_failed`, `result_downloaded`) sin enviar entradas ni resultados.
3. Sustituir los supuestos sintéticos e ilustrativos por fuentes aprobadas, manteniendo la evidencia junto a cada número.
4. Decidir el despliegue público definitivo del API —FastAPI protegido detrás de Cloudflare o Workers como fachada— sin cambiar el contrato `/api/v1`.
5. Revisar los avisos restantes de `npm audit` cuando exista una actualización compatible de las dependencias de build.

## Preview local de esta sesión

La exportación estática y FastAPI se pueden servir juntos con:

```bash
SUITE_ACTUARIAL_FRONTEND=/home/exedev/repos/suite-actuarial/frontend/out \
  .venv/bin/uvicorn suite_actuarial.api.main:app --host 0.0.0.0 --port 8000
```

No se guardan claves de PostHog en el repositorio.
