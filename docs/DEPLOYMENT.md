# Despliegue

Dos entornos. El dashboard estatico vive en Cloudflare Pages; el calculo vive en
Cloud Run. En produccion, delante del calculo hay un worker de Cloudflare que es
la unica direccion que el publico alcanza.

| Rama | Sitio | API | Acceso |
| --- | --- | --- | --- |
| `main` | `suite.gonor.me` (Pages, produccion) | `api-suite.gonor.me` -> worker `suite-actuarial-api` -> Cloud Run `suite-actuarial` | Publico, con limite de tasa |
| `dev` | `dev-suite.gonor.me` (Pages, rama `dev`) | mismo origen, `/api/*` -> Cloud Run `suite-actuarial-dev` | Cloudflare Access (PIN por correo) |

Dev no pasa por el borde: esta detras de Access, lo usa una persona, y el
proxy de Pages ya le da un solo origen. El borde resuelve un problema que dev
no tiene.

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

## El borde publico (`edge/`)

El worker vive en [`edge/`](../edge/) y su documentacion propia esta en
[`edge/README.md`](../edge/README.md). Hace cuatro cosas que Cloud Run no puede
hacer por si mismo, porque las cuatro tienen que ocurrir antes de que la
peticion cueste algo: limite de tasa, CORS publico, cache de la configuracion
anual, y analitica de lo que el origen nunca ve.

### Por que el API no corre en Workers

La pregunta aparece sola al ver un worker delante. No corre ahi, y no es una
preferencia:

| Obstaculo | Detalle |
| --- | --- |
| `scipy` | `danos/frecuencia_severidad.py` usa `scipy.stats`. No esta en el conjunto soportado por Cloudflare y la rueda de Pyodide supera con mucho el limite de 10 MB comprimidos. |
| `pandas` | Se importa en quince modulos y en `routers/reserves.py`. Cloudflare documenta soporte limitado. |
| Memoria | 128 MB por aislado, compartidos con Pyodide, numpy y pandas. |
| CPU | 10 ms por peticion en el plan gratuito. |

Ademas, portarlo a Pyodide re-alojaria la matematica actuarial en un entorno
contra el que la suite de pruebas nunca ha corrido. Eso es exactamente lo que
`AGENTS.md` protege. El worker no calcula: proxia.

### Ruta, no dominio personalizado

`api-suite.gonor.me` ya existe como CNAME proxiado al mapeo de dominio de Cloud
Run, y un dominio personalizado de Workers no puede tomar un nombre que ya
tiene CNAME sin borrar el registro y dejar el API caido mientras el DNS se
asienta. Una ruta se superpone al registro existente: el cambio es inmediato y
borrarla restaura el camino anterior igual de rapido. Esa es la reversion.

### Por que el origen exige una cabecera

El servicio `suite-actuarial` tenia la URL `run.app` deshabilitada
(`default-url-disabled`), asi que solo se alcanzaba por el mapeo de dominio.
Para que el worker tenga a donde llamar hay que reactivarla, y una URL publica
mas es un rodeo sin limite de tasa alrededor del borde.

Por eso produccion pasa a definir `SUITE_PROXY_SHARED_SECRET`, el mismo
mecanismo que ya amurallaba dev (`require_proxy_secret` en `api/main.py`). El
worker anade la cabecera del lado del servidor; una peticion directa a la URL
`run.app` recibe 404. El borde deja de ser la puerta principal y pasa a ser la
unica.

**El orden importa.** Con el secreto puesto y sin la ruta del worker viva,
`api-suite.gonor.me` responde 404 a todo el mundo. Primero la ruta, despues el
secreto.

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
- `PROXY_SHARED_SECRET` — el de dev. Lo comparten el servicio
  `suite-actuarial-dev` y el proxy de Pages, asi que rotarlo obliga a tocar los
  dos.
- `PROXY_SHARED_SECRET_PROD` — el de produccion, distinto a proposito. Se
  inyecta en `suite-actuarial` como `SUITE_PROXY_SHARED_SECRET` y tiene que
  coincidir con el secreto `PROXY_SHARED_SECRET` del worker de `edge/`. Cierra
  la URL `run.app` para que el borde sea la unica entrada. Dos entornos, dos
  secretos: reutilizar uno solo obligaria a rotar tres cosas a la vez.
- `POSTHOG_PROJECT_API_KEY` — inyectado por `deploy.yml`. Sin el, el codigo de
  telemetria de `api/telemetry.py` existe pero no envia nada, que es lo que
  ocurrio desde que se escribio hasta el 2026-08-02.

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

**Cloudflare Workers** — worker `suite-actuarial-api`, definido en `edge/`. No
se despliega desde GitHub Actions; se publica con `npx wrangler deploy` desde
`edge/`. Recursos que hay que crear una sola vez:

- Namespace de KV `API_KEYS`, cuyo id va en `edge/wrangler.jsonc`.
- Secretos del worker: `POSTHOG_PROJECT_API_KEY` y `PROXY_SHARED_SECRET` (el
  mismo valor que tiene Cloud Run), con `npx wrangler secret put`.
- Ruta `api-suite.gonor.me/*` en la zona `gonor.me`, declarada en
  `wrangler.jsonc`.
- La URL por omision del servicio `suite-actuarial` tiene que estar activa
  (`--default-url`), porque es la direccion a la que el worker llama.

El subdominio `workers.dev` de la cuenta es `andtega349`. El worker lo tiene
desactivado (`"workers_dev": false`): no es un nombre para poner delante de un
API publico, y una segunda direccion viva solo seria una forma de esquivar la
ruta y su limite de tasa.

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

La capa que faltaba —la que va delante y no detras— **ya existe**: el worker de
`edge/` limita a 120 peticiones por minuto por IP, y a 1200 con clave. El abuso
se rechaza en Cloudflare, antes de tocar Cloud Run.

Dos limites de esa proteccion, que conviene tener presentes. El primero se midio
contra el despliegue real el 2026-08-02 y result ser mas severo de lo que
sugiere la documentacion:

- **El conteo es por maquina del borde, no por centro de datos ni global.**
  250 peticiones sobre una sola conexion reutilizada cortaron cerca de la 108;
  200 peticiones sobre 25 conexiones en paralelo **no cortaron ninguna**, todas
  desde la misma IP y el mismo colo (LAX). Quien abre conexiones en paralelo
  recibe una cuota por cada maquina que le toque. Esto frena a un raspador
  ingenuo y no frena a uno distribuido. Cloudflare lo describe como una API
  «permisiva, eventualmente consistente, y disenada a proposito para no usarse
  como sistema de contabilidad exacto».
- **`--max-instances` sigue siendo el unico limite duro de facturacion.** El
  borde reduce la probabilidad de llegar a el; no lo sustituye. Esa frase valia
  antes del borde y sigue valiendo despues.

Si algun dia hace falta un techo firme, hay dos caminos, ambos con costo: una
regla de Rate Limiting del WAF a nivel de zona, o un Durable Object que lleve la
cuenta central. Ninguno es necesario hoy.

Sigue pendiente una **alerta de presupuesto** en la cuenta de facturacion. La
API `billingbudgets.googleapis.com` esta deshabilitada en el proyecto; hay que
activarla antes de poder crearla.

## Rollback

Cada despliegue etiqueta la imagen con el SHA. Para volver atras:

```bash
gcloud run deploy suite-actuarial \
  --image=us-central1-docker.pkg.dev/project-ad7a5be2-a1c7-4510-82d/suite-actuarial/dashboard:<SHA> \
  --region=us-central1
```

### Revertir el borde

Quitar la ruta devuelve `api-suite.gonor.me` al mapeo de dominio de Cloud Run,
que sigue existiendo intacto:

```bash
cd edge && npx wrangler triggers delete --routes "api-suite.gonor.me/*"
```

Si produccion ya tiene `SUITE_PROXY_SHARED_SECRET`, hay que quitarlo en el mismo
movimiento; si no, el API responde 404 a todo el mundo:

```bash
gcloud run services update suite-actuarial --region=us-central1 \
  --remove-env-vars=SUITE_PROXY_SHARED_SECRET
```
