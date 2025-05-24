FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  ACTIVE_DB_BACKEND="postgres" \
  APP_PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
# COPY config.py .

EXPOSE ${APP_PORT}

CMD ["python", "-m", "src.main"]
