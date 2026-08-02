# Borde público del API

Worker de Cloudflare que atiende `api-suite.gonor.me`. Es la primera cosa que toca
una petición y la única dirección que el público alcanza.

No contiene lógica actuarial y no debe contenerla. Cada número de cada respuesta lo
calcula el paquete de Python que corre detrás, en Cloud Run. El worker es la puerta,
no el cerebro.

## Por qué existe

Cuatro trabajos que el servicio de Cloud Run no puede hacer por sí mismo, porque los
cuatro tienen que ocurrir **antes** de que la petición cueste algo:

| Trabajo | Razón de estar delante |
| --- | --- |
| Límite de tasa | El abuso se rechaza en Cloudflare, donde es gratis. Una petición que llega a Cloud Run ya arrancó un contenedor y ya cuesta dinero. |
| CORS | Aquí se permite a terceros llamar desde un navegador, sin ampliar la lista del origen, que sigue nombrando sólo al tablero. |
| Caché | La configuración regulatoria anual es idéntica para todos, así que servirla desde el borde no despierta ningún contenedor. |
| Analítica | El borde ve lo que el origen no puede ver: peticiones frenadas por límite de tasa, aciertos de caché y un origen que no respondió. |

Antes de esto, `docs/DEPLOYMENT.md` señalaba la primera fila como la capa que
faltaba. El techo de gasto era `--max-instances`; ahora hay una capa delante.

## Acceso

El API es abierto. Quien no presenta clave se atiende igual, con el límite bajo.
Una clave sólo sube ese límite y añade una etiqueta a la analítica: es un mecanismo
de contabilidad, no una reja.

| Nivel | Límite | Se cuenta contra |
| --- | --- | --- |
| Anónimo | 120 peticiones/minuto | IP del cliente |
| Con clave | 1200 peticiones/minuto | Digest de la clave |

### Qué tan firme es el techo

El límite **no es global, y es más granular que «por centro de datos»**. Cloudflare
cuenta contra un valor cacheado localmente en cada máquina del borde. Medido contra
este despliegue el 2026-08-02:

| Prueba | Resultado |
| --- | --- |
| 250 peticiones sobre una sola conexión reutilizada | Cortó cerca de la 108 y devolvió 429 el resto |
| 200 peticiones sobre 25 conexiones en paralelo | **No cortó ni una** |

La segunda fila es el límite real de esta protección: quien abre conexiones en
paralelo obtiene una cuota por cada máquina que le toque. Frena a un raspador ingenuo
—un bucle sobre una conexión— y no frena a uno distribuido.

La documentación de Cloudflare lo dice sin rodeos: la API es «permisiva,
eventualmente consistente, y diseñada a propósito para no usarse como sistema de
contabilidad exacto».

Si algún día hace falta un techo firme, hay dos caminos, ambos con costo: una regla
de Rate Limiting del WAF a nivel de zona, o un Durable Object que lleve la cuenta
central. Ninguno es necesario hoy: `--max-instances` en Cloud Run sigue siendo el
único límite duro de facturación, y no ha cambiado.

El límite anónimo es 120 y no 60 porque el tablero es uno de esos consumidores:
`useLiveCalculation` espera 350 ms de quietud, así que quien mueve un deslizador
supera de forma legítima una petición por segundo. Un límite que hace que la propia
interfaz devuelva 429 no es protección, es un defecto.

Una clave presentada pero no reconocida se rechaza con 401, no se degrada en
silencio a anónimo. Degradarla convertiría una errata en la clave en un 429
inexplicable mucho después.

### Presentar una clave

```bash
curl -H "Authorization: Bearer <clave>" https://api-suite.gonor.me/api/v1/config/2026/uma
curl -H "X-API-Key: <clave>"            https://api-suite.gonor.me/api/v1/config/2026/uma
```

### Emitir una clave

En KV se guarda el SHA-256 de la clave, nunca la clave. Leer el namespace no
devuelve nada utilizable.

```bash
CLAVE=$(openssl rand -hex 24)
DIGEST=$(printf '%s' "$CLAVE" | openssl dgst -sha256 -hex | awk '{print $2}')
npx wrangler kv key put --binding=API_KEYS --remote "$DIGEST" '{"label":"nombre-del-consumidor"}'
echo "Entregar esta clave una sola vez: $CLAVE"
```

La etiqueta es lo que aparece en PostHog. No pongas datos personales en ella.

## Caché

Sólo se cachean `GET /api/info` y `GET /api/v1/config/*`: son idénticos para
cualquiera y cambian sólo con un despliegue. El resto del API son cálculos POST que
llevan los supuestos de quien llama, así que no hay nada compartido que cachear y
cachear uno sería un error de corrección, no una lectura vieja.

`CACHE_TTL_SECONDS` (300 por omisión) fija la frescura. La cabecera `X-Edge-Cache`
declara `hit`, `miss` o `bypass` en cada respuesta.

### Después de un despliegue, el borde sirve viejo hasta cinco minutos

Ocurrió al desplegar 2.2.0 y conviene esperarlo: `/api/info` siguió reportando
`"version": "2.1.0"` durante minutos después de que la revisión nueva ya estaba
sirviendo. No era un despliegue fallido, era la caché del borde entregando la entrada
anterior hasta que expiró su TTL.

Para comprobar una versión recién desplegada, salta la caché con un parámetro
cualquiera:

```bash
curl "https://api-suite.gonor.me/api/info?cb=$(openssl rand -hex 6)"
```

Vale la pena tenerlo presente al verificar un despliegue: sin esto es fácil concluir
que no subió cuando sí subió.

## Verificación

```bash
npm ci
npm run typecheck
npm test
```

Las pruebas corren dentro de workerd, el mismo runtime que sirve producción. Ambas
compuertas corren en CI.

## Despliegue

```bash
npx wrangler deploy --env verify   # ensayo, en workers.dev, sin ruta
npx wrangler deploy                # produccion, en api-suite.gonor.me
```

El entorno `verify` corre el mismo codigo contra el mismo origen, pero sin ruta
adjunta, asi que se puede ejercitar de punta a punta sin que `api-suite.gonor.me`
cambie de comportamiento para nadie. Tiene su propio namespace de KV: una clave de
prueba nunca debe autenticar contra produccion.

Requiere que existan el namespace de KV y los secretos; ver
[`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md). Los secretos se ponen por entorno:

```bash
npx wrangler secret put POSTHOG_PROJECT_API_KEY --env verify
npx wrangler secret put POSTHOG_PROJECT_API_KEY
```

| Secreto | Para qué |
| --- | --- |
| `POSTHOG_PROJECT_API_KEY` | Sin él, el borde no envía ninguna analítica. |
| `PROXY_SHARED_SECRET` | Cabecera que el origen exige. Sin ella, la URL `run.app` sería un rodeo sin límite de tasa alrededor del borde. |
