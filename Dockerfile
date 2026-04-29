# --- builder ---
FROM python:3.12-slim as builder
WORKDIR /app

RUN apt-get update && apt-get install -y gcc graphviz && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

# --- runtime ---
FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y curl graphviz && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

COPY src/ src/

RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "al_furqan.api.app:app", "--host", "0.0.0.0", "--port", "8000"]