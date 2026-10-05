FROM python:3.12.15-slim@sha256:29113dcae7aad06daa8e95260fa09f27d62be33b9687ea3774f771d601a02256
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY requirements.lock .
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock && python -m pip check
COPY . .
RUN useradd --uid 10001 --create-home app
USER app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
