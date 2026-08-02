# API-only image. The dashboard is built and served by Cloudflare Pages; this
# container is the backend behind it. Dropping the Node build stage keeps the
# image small and gives each layer a single owner.
#
# The static export is no longer copied in, so `SUITE_ACTUARIAL_FRONTEND` finds
# no directory and the app keeps a JSON root response instead of mounting a site.
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

# No se copia ningun `data/` de la raiz: no existe. La tabla de mortalidad vive
# dentro del paquete (`src/suite_actuarial/data/mortality_tables/`), la trae la
# linea de arriba y `pyproject.toml` la declara como package-data. La copia de
# la raiz era un duplicado que se elimino al dejar una sola ruta de carga; la
# instruccion se quedo atras y rompia la imagen con "/data: not found".

RUN pip install --no-cache-dir -e ".[api]"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "uvicorn", "suite_actuarial.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
