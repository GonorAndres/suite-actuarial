FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY data/ data/
COPY streamlit_app/ streamlit_app/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[api,viz]"

# Default: run the API
EXPOSE 8000
CMD ["uvicorn", "mexican_insurance.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
