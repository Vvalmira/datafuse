import json
import os
from typing import Any

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
JOB_TTL_SECONDS = 3600

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _client


def job_key(job_id: str) -> str:
    return f"job:{job_id}"


def progress_key(job_id: str) -> str:
    return f"job:{job_id}:completed"


def save_job(job_id: str, payload: dict[str, Any]) -> None:
    get_redis().setex(job_key(job_id), JOB_TTL_SECONDS, json.dumps(payload))


def load_job(job_id: str) -> dict[str, Any] | None:
    raw = get_redis().get(job_key(job_id))
    if raw is None:
        return None
    return json.loads(raw)


def update_job(job_id: str, **updates: Any) -> dict[str, Any]:
    current = load_job(job_id) or {}
    current.update(updates)
    save_job(job_id, current)
    return current


def init_progress_counter(job_id: str) -> None:
    client = get_redis()
    key = progress_key(job_id)
    client.setex(key, JOB_TTL_SECONDS, 0)


def increment_completed_chunks(job_id: str) -> int:
    client = get_redis()
    key = progress_key(job_id)
    completed = int(client.incr(key))
    client.expire(key, JOB_TTL_SECONDS)
    return completed
