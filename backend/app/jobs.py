from collections import Counter
from time import perf_counter
from typing import Any
from uuid import uuid4
import re

from celery import chord

from app.celery_app import celery_app
from app.redis_store import increment_completed_chunks, init_progress_counter, save_job, update_job

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def split_text(text: str, chunk_size: int) -> list[str]:
    words = WORD_RE.findall(text)
    if not words:
        return [text]
    return [" ".join(words[index : index + chunk_size]) for index in range(0, len(words), chunk_size)]


def analyze_text_chunk(chunk: str, chunk_index: int) -> dict[str, Any]:
    started = perf_counter()
    words = [word.lower() for word in WORD_RE.findall(chunk)]
    counts = Counter(words)
    return {
        "chunk_index": chunk_index,
        "word_count": len(words),
        "character_count": len(chunk),
        "term_counts": dict(counts),
        "top_terms": counts.most_common(5),
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
    }


def aggregate_chunk_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    started = perf_counter()
    total_terms: Counter[str] = Counter()
    word_count = 0
    character_count = 0

    sorted_results = sorted(results, key=lambda item: item["chunk_index"])
    for result in sorted_results:
        word_count += int(result["word_count"])
        character_count += int(result["character_count"])
        total_terms.update(result.get("term_counts", {}))

    return {
        "word_count": word_count,
        "character_count": character_count,
        "top_terms": total_terms.most_common(10),
        "chunks": [{key: value for key, value in result.items() if key != "term_counts"} for result in sorted_results],
        "elapsed_ms": round((perf_counter() - started) * 1000, 3),
    }


def create_text_job(text: str, chunk_size: int) -> str:
    job_id = str(uuid4())
    chunks = split_text(text, chunk_size)
    save_job(
        job_id,
        {
            "job_id": job_id,
            "state": "queued",
            "progress": {"completed_chunks": 0, "total_chunks": len(chunks)},
            "result": None,
            "error": None,
        },
    )
    init_progress_counter(job_id)

    header = [analyze_chunk.s(chunk, index, job_id) for index, chunk in enumerate(chunks)]
    callback = finalize_job.s(job_id)
    chord(header)(callback)
    return job_id


@celery_app.task(name="jobs.analyze_chunk")
def analyze_chunk(chunk: str, chunk_index: int, job_id: str) -> dict[str, Any]:
    update_job(job_id, state="running")
    result = analyze_text_chunk(chunk, chunk_index)
    completed = increment_completed_chunks(job_id)
    from app.redis_store import load_job

    current = load_job(job_id) or {}
    progress = current.get("progress", {})
    update_job(
        job_id,
        state="running",
        progress={
            "completed_chunks": completed,
            "total_chunks": int(progress.get("total_chunks", 0)),
        },
    )
    return result


@celery_app.task(name="jobs.finalize_job")
def finalize_job(results: list[dict[str, Any]], job_id: str) -> dict[str, Any]:
    try:
        aggregate = aggregate_chunk_results(results)
        update_job(
            job_id,
            state="completed",
            progress={"completed_chunks": len(results), "total_chunks": len(results)},
            result=aggregate,
            error=None,
        )
        return aggregate
    except Exception as exc:
        update_job(job_id, state="failed", error=str(exc))
        raise
