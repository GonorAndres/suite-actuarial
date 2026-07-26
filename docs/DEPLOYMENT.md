# Despliegue

Dos entornos. El dashboard estatico vive en Cloudflare Pages; el API vive en
Cloud Run. Cada rama publica su propio par.

| Rama | Sitio | API | Acceso |
| --- | --- | --- | --- |
| `main` | `suite.gonor.me` (Pages, produccion) | `api-suite.gonor.me` -> Cloud Run `suite-actuarial` | Publico |
| `dev` | `dev-suite.gonor.me` (Pages, rama `dev`) | mismo origen, `/api/*` -> Cloud Run `suite-actuarial-dev` | Cloudflare Access (PIN por correo) |

## Como se dispara

`.github/workflows/ci.yml` corre en cada push de cualquier rama.

El backend usa `deploy.yml`: escucha `workflow_run` de CI y solo actua si
termino en verde y la rama es `main` o `dev`. Esto cierra un hueco anterior:
antes se disparaba con `push` en paralelo a CI, asi que una compuerta en rojo
no impedia publicar.

El dashboard no usa GitHub Actions. El proyecto `suite-actuarial` en Cloudflare
Pages esta conectado directamente al repositorio: Cloudflare clona, corre
`npm run build` y publica el resultado el solo, en cuanto detecta un push a
`main` o `dev`. No hay compuerta de CI de por medio en ese camino — si hace
falta bloquear un build roto, es configuracion de Cloudflare Pages, no de este
repositorio.

## Por que dev usa un proxy y no una llamada directa

El sitio de dev sirve `/api/*` desde su propio origen mediante un worker de
Pages (`frontend/cloudflare/_worker.js`). Dos consecuencias:

1. **Una sola politica de Access cubre sitio y API.** Si el navegador llamara
   directo a Cloud Run, esa llamada no pasaria por Access y el API quedaria
   abierto aunque el sitio estuviera amurallado.
2. **No hay origen cruzado**, asi que dev no necesita CORS.

El worker anade `X-Proxy-Secret` del lado del servidor. El navegador nunca ve el
secreto. El backend de dev rechaza con 404 —no 403— cualquier peticion sin esa
cabecera: un despliegue amurallado no deberia confirmar que existe. La logica
esta en `require_proxy_secret` (`api/main.py`) y solo se activa cuando
`SUITE_PROXY_SHARED_SECRET` esta definida, asi que produccion sigue publica.

Un token de IAM de Cloud Run no sirve aqui: el navegador no puede adjuntarlo.
Por eso el muro es la cabecera compartida y no `--no-allow-unauthenticated`.

## Por que `api-suite` y no `api.suite`

El nombre lleva guion, no punto, y no es una preferencia estetica. El
certificado gratuito de Cloudflare (Universal SSL) cubre exactamente
`gonor.me` y `*.gonor.me`: un solo nivel. `api.suite.gonor.me` esta dos niveles
abajo, asi que el borde de Cloudflare no tiene certificado para el y el
handshake TLS falla en cuanto se activa el proxy. Emitirlo requiere Advanced
Certificate Manager, 10 USD al mes.

`api-suite.gonor.me` cae dentro del comodin y funciona proxiado sin costo. El
mismo limite aplica a cualquier API futura: `api-loquesea.gonor.me` es gratis,
`api.loquesea.gonor.me` no.

## CORS

`SUITE_CORS_ORIGINS` es una lista separada por comas. Sin ella, el valor por
defecto cubre solo `localhost:3000`. `allow_credentials` esta apagado: el API no
usa cookies ni sesion.

## Configuracion en las cuentas (ya realizada, 2026-07-26)

Nada de esto vive en el repositorio; queda anotado aqui por si hay que
recrearlo.

**GitHub -> Settings -> Secrets** (usados solo por `deploy.yml`, el backend)
- `CLOUDFLARE_API_TOKEN` — ya no lo usa ningun workflow tras retirar
  `deploy-frontend.yml`, pero se deja creado por si un despliegue manual con
  `wrangler` lo necesita.
- `CLOUDFLARE_ACCOUNT_ID` (`9e88860c389c87f4ec09baa1e9675a61`)
- `PROXY_SHARED_SECRET` — inyectado por `deploy.yml` en el servicio
  `suite-actuarial-dev` como `SUITE_PROXY_SHARED_SECRET`.

**Cloudflare Pages** — proyecto `suite-actuarial`, conectado por Git a
`GonorAndres/suite-actuarial` (rama de produccion `main`, previews solo para
`dev`). Dominios: `suite.gonor.me` (produccion) y `dev-suite.gonor.me`
(alias de la rama `dev`). Variables de entorno por entorno:
- Produccion: `NEXT_PUBLIC_API_URL=https://api-suite.gonor.me/api/v1`
- Preview (`dev`): `NEXT_PUBLIC_API_URL=/api/v1`, `API_ORIGIN` = URL de Cloud
  Run de `suite-actuarial-dev`, `PROXY_SHARED_SECRET` = el mismo secreto que
  arriba.

El comando de build (`npm run build && ...`) copia `cloudflare/_worker.js` a
la salida solo cuando `$CF_PAGES_BRANCH` es `dev`, para que produccion no
cargue el proxy.

**Cloudflare Access** — aplicacion sobre `dev-suite.gonor.me`, politica de
permitir por correo (sin PIN adicional: el IdP ya es One-time PIN a nivel de
cuenta).

**Cloud Run** — el servicio `suite-actuarial-dev` lo crea el primer despliegue
de la rama `dev`.

## Identidad de ejecucion

Ambos servicios corren como `suite-actuarial-run@…iam.gserviceaccount.com`, una
cuenta creada para esto y **sin ningun rol de IAM**. No es un descuido: el
servicio lee datos empaquetados en la imagen y no llama a ninguna API de Google,
asi que no necesita permisos. Antes usaban la cuenta de computo por defecto, que
trae permisos amplios sobre todo el proyecto — mas autoridad de la que un
servicio publico deberia tener si alguien lo compromete.

Si algun dia el servicio necesita leer un bucket o publicar en Pub/Sub, se le
concede ese rol especifico a esta cuenta, no a la de por defecto.

## Contencion del gasto

El techo real de facturacion en Cloud Run es `--max-instances`. Lo demas reduce
la probabilidad de llegar a el; solo ese parametro lo acota.

| Control | Produccion | Dev | Que acota |
| --- | --- | --- | --- |
| `--max-instances` | 2 | 1 | Contenedores simultaneos: el techo duro |
| `--concurrency` | 80 | 80 | Peticiones por contenedor antes de escalar |
| `--min-instances` | 0 | 0 | Sin costo en reposo; a cambio, arranque en frio |
| `--timeout` | 60s | 60s | Una peticion colgada no factura 5 minutos |
| `--cpu-throttling` | si | si | Solo se cobra CPU mientras se atiende la peticion |

Con `max-instances=2`, el peor caso concebible —dos contenedores saturados las
24 horas del mes— ronda los 130 USD, antes de descontar la capa gratuita. No es
cero: si el objetivo es que un abuso no pueda pasar de una cifra conocida, bajar
`max-instances` a 1 la reduce a la mitad, al costo de servir menos trafico
legitimo en un pico.

Falta la capa mas util, que va delante y no detras: **limitacion de tasa en
Cloudflare** sobre `api-suite.gonor.me`. Una regla por IP corta el abuso antes de que
llegue a Cloud Run, donde ya cuesta dinero. Requiere que el token tenga alcance
de WAF/Rate Limiting.

Conviene ademas una **alerta de presupuesto** en la cuenta de facturacion. La
API `billingbudgets.googleapis.com` esta deshabilitada en el proyecto; hay que
activarla antes de poder crearla.

## Rollback

Cada despliegue etiqueta la imagen con el SHA. Para volver atras:

```bash
gcloud run deploy suite-actuarial \
  --image=us-central1-docker.pkg.dev/project-ad7a5be2-a1c7-4510-82d/suite-actuarial/dashboard:<SHA> \
  --region=us-central1
```
