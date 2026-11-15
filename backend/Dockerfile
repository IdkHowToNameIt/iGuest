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

# Local dev (docker-compose): apply migrations, then serve with hot-reload.
# In production (Render) migrations run via the Pre-Deploy Command instead,
# and $PORT is injected by the platform.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload"]
