FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
COPY data/ data/
COPY docs/ docs/
COPY streamlit_app/ streamlit_app/

RUN pip install --no-cache-dir -e ".[viz]"

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app/Home.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
