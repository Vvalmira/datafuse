"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type JobState = "queued" | "running" | "completed" | "failed";

type ChunkResult = {
  chunk_index: number;
  word_count: number;
  character_count: number;
  top_terms: [string, number][];
  elapsed_ms: number;
};

type JobStatus = {
  job_id: string;
  state: JobState;
  progress: {
    completed_chunks: number;
    total_chunks: number;
  };
  result: null | {
    word_count: number;
    character_count: number;
    top_terms: [string, number][];
    chunks: ChunkResult[];
    elapsed_ms: number;
  };
  error: string | null;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const sampleText =
  "FastAPI receives a request, Celery fans the work out to parallel workers, Redis keeps the job state, and this tiny UI polls until the aggregate text analysis is ready.";

export default function Home() {
  const [text, setText] = useState(sampleText);
  const [chunkSize, setChunkSize] = useState(50);
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const progressPercent = useMemo(() => {
    if (!job || job.progress.total_chunks === 0) return 0;
    return Math.round((job.progress.completed_chunks / job.progress.total_chunks) * 100);
  }, [job]);

  useEffect(() => {
    if (!jobId || job?.state === "completed" || job?.state === "failed") return;

    const poll = async () => {
      const response = await fetch(`${apiUrl}/api/jobs/${jobId}`);
      if (!response.ok) throw new Error("Could not load job status");
      setJob(await response.json());
    };

    poll().catch((pollError: Error) => setError(pollError.message));
    const timer = window.setInterval(() => {
      poll().catch((pollError: Error) => setError(pollError.message));
    }, 1000);

    return () => window.clearInterval(timer);
  }, [jobId, job?.state]);

  async function submitJob(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    setJob(null);

    try {
      const response = await fetch(`${apiUrl}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, chunk_size: chunkSize })
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Could not submit job");
      }

      const created: { job_id: string } = await response.json();
      setJobId(created.job_id);
      setJob({
        job_id: created.job_id,
        state: "queued",
        progress: { completed_chunks: 0, total_chunks: 0 },
        result: null,
        error: null
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unexpected submit error");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="shell">
      <section className="intro">
        <div>
          <p className="eyebrow">Distributed compute demo</p>
          <h1>Datafuse Text Lab</h1>
        </div>
        <p>
          Submit text, split it into parallel Celery tasks, and watch FastAPI report progress from Redis as the
          aggregate result comes together.
        </p>
      </section>

      <section className="workspace">
        <form className="panel formPanel" onSubmit={submitJob}>
          <label htmlFor="text">Text payload</label>
          <textarea id="text" value={text} onChange={(event) => setText(event.target.value)} />

          <label htmlFor="chunkSize">Words per task</label>
          <input
            id="chunkSize"
            min={50}
            max={5000}
            type="number"
            value={chunkSize}
            onChange={(event) => setChunkSize(Number(event.target.value))}
          />

          <button disabled={isSubmitting || text.trim().length === 0} type="submit">
            {isSubmitting ? "Submitting..." : "Run analysis"}
          </button>
          {error ? <p className="error">{error}</p> : null}
        </form>

        <section className="panel resultPanel" aria-live="polite">
          <div className="statusHeader">
            <div>
              <p className="eyebrow">Job status</p>
              <h2>{job ? job.state : "idle"}</h2>
            </div>
            {job ? <code>{job.job_id}</code> : null}
          </div>

          <div className="progressTrack">
            <div className="progressFill" style={{ width: `${progressPercent}%` }} />
          </div>
          <p className="muted">
            {job
              ? `${job.progress.completed_chunks} of ${job.progress.total_chunks} chunks completed`
              : "Submit a job to start polling."}
          </p>

          {job?.error ? <p className="error">{job.error}</p> : null}

          {job?.result ? (
            <div className="results">
              <div className="metrics">
                <Metric label="Words" value={job.result.word_count.toLocaleString()} />
                <Metric label="Characters" value={job.result.character_count.toLocaleString()} />
                <Metric label="Chunks" value={job.result.chunks.length.toLocaleString()} />
                <Metric label="Aggregate ms" value={job.result.elapsed_ms.toLocaleString()} />
              </div>

              <h3>Top terms</h3>
              <div className="terms">
                {job.result.top_terms.map(([term, count]) => (
                  <span key={term}>
                    {term} <strong>{count}</strong>
                  </span>
                ))}
              </div>

              <h3>Chunk results</h3>
              <div className="chunkList">
                {job.result.chunks.map((chunk) => (
                  <div className="chunk" key={chunk.chunk_index}>
                    <strong>Chunk {chunk.chunk_index + 1}</strong>
                    <span>{chunk.word_count} words</span>
                    <span>{chunk.elapsed_ms} ms</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </section>
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
