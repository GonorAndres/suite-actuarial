# Laboratorio web de suite_actuarial

Interfaz bilingüe para construir y examinar experimentos actuariales. Presenta primero
el propósito, los beneficios y los supuestos; los detalles de integración son secundarios.

## Desarrollo

```bash
npm ci
npm run dev
```

La interfaz espera el backend en `http://localhost:8000/api/v1`. Puede cambiarse con
`NEXT_PUBLIC_API_URL`. Para incrustar el video insignia, define
`NEXT_PUBLIC_DEMO_VIDEO_ID` con el identificador de YouTube.

## Verificación y exportación

```bash
npm run lint
npm run build
```

Next.js genera un sitio estático en `out/`. La imagen de producción lo copia junto al
paquete Python y FastAPI lo sirve como la experiencia principal; las rutas técnicas
permanecen bajo `/api/v1`, `/api/info` y `/docs`.

La entrada principal está en `src/app/page.tsx`, el laboratorio guiado en
`src/app/lab/page.tsx` y los estilos de estudio científico en `src/app/globals.css`.
