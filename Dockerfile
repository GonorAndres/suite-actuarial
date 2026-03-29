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

# Inject Google Analytics into Streamlit's index.html
RUN STHTML=$(python -c "import streamlit,os;print(os.path.join(os.path.dirname(streamlit.__file__),'static','index.html'))") && \
    sed -i 's|</head>|<script async src="https://www.googletagmanager.com/gtag/js?id=G-098V02NCB0"></script><script>window.dataLayer=window.dataLayer\|\|[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-098V02NCB0");</script></head>|' "$STHTML"

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app/Home.py", \
     "--server.port=8080", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
