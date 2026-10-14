FROM logistics-rag-backend:phase1
USER root
WORKDIR /app/backend
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libcairo2 \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pgvector==0.3.6 openai==1.50.0 weasyprint==70.0
COPY . .
RUN chown -R app:app /app/backend
USER app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
