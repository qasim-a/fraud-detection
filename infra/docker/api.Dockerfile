FROM python:3.12-slim

WORKDIR /app
COPY backend /app
RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["uvicorn", "fraud_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
