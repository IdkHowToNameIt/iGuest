# Backend image: FastAPI + uvicorn. Kept minimal (python-slim); the app source is
# mounted as a volume in docker-compose for hot-reload, so a rebuild is only needed
# when requirements.txt changes.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so the layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Apply migrations, then serve. --reload picks up edits from the mounted source.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
