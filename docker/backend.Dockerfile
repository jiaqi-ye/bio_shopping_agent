FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --upgrade openai

COPY backend /app/backend
COPY db /app/db

ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/db/procurement.db

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
