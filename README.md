# Datafuse Text Lab

A tiny local demo for distributed background computation with FastAPI, Celery,
Redis, and Next.js.

The app lets you paste text into a web form, submit it as a background job,
split the work into parallel Celery tasks, poll progress by job ID, and display
aggregate text-analysis results when the worker finishes.

## Run locally

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- FastAPI docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## API flow

Submit a job:

```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"text":"FastAPI starts work and Celery runs chunks in parallel.", "chunk_size":50}'
```

Poll the returned ID:

```bash
curl http://localhost:8000/api/jobs/<job_id>
```

Job states are `queued`, `running`, `completed`, and `failed`. Completed jobs
include total words, total characters, top terms, per-chunk results, and timing.

## Project structure

```text
backend/
  app/
    main.py          # FastAPI routes
    celery_app.py    # Celery configuration
    jobs.py          # chunking, analysis, Celery tasks
    redis_store.py   # ephemeral job metadata in Redis
    schemas.py       # Pydantic request/response models
  tests/
frontend/
  app/
docker-compose.yml
```

## Tests

Run the backend smoke tests in Docker:

```bash
docker compose run --rm api python -m pytest tests
```

## Notes

- Redis is used as the Celery broker, Celery result backend, and lightweight job
  metadata store.
- Results are ephemeral and expire after one hour.
- This is a local demo: no authentication, persistent database, or production
  deployment config.
