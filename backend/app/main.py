from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.jobs import create_text_job
from app.redis_store import load_job
from app.schemas import JobCreate, JobCreated, JobStatus

app = FastAPI(title="Datafuse Text Lab", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/jobs", response_model=JobCreated)
def submit_job(payload: JobCreate) -> JobCreated:
    return JobCreated(job_id=create_text_job(payload.text, payload.chunk_size))


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str) -> dict:
    job = load_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
