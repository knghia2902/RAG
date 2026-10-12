FROM logistics-rag-backend:phase1
USER root
WORKDIR /app/backend
RUN pip install --no-cache-dir pgvector==0.3.6 openai==1.50.0
COPY . .
RUN chown -R app:app /app/backend
USER app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
