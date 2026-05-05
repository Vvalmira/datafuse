from typing import Literal

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=100_000)
    chunk_size: int = Field(500, ge=50, le=5_000)


class JobCreated(BaseModel):
    job_id: str


class JobProgress(BaseModel):
    completed_chunks: int = 0
    total_chunks: int = 0


class ChunkResult(BaseModel):
    chunk_index: int
    word_count: int
    character_count: int
    top_terms: list[tuple[str, int]]
    elapsed_ms: float


class AggregateResult(BaseModel):
    word_count: int
    character_count: int
    top_terms: list[tuple[str, int]]
    chunks: list[ChunkResult]
    elapsed_ms: float

# JobStatus represents the current status of a job, including its progress and result if completed.
class JobStatus(BaseModel):
    job_id: str
    state: Literal["queued", "running", "completed", "failed"]
    progress: JobProgress
    result: AggregateResult | None = None
    error: str | None = None
