import { EVENT_TYPES } from "./types";
import type { JobResponse, PagesResponse, ProgressEvent } from "./types";

const API_BASE = "/api/v1";

export async function fetchDefaultPreamble(): Promise<string> {
  const res = await fetch(`${API_BASE}/preamble/default`);
  if (!res.ok) throw new Error("Failed to fetch default preamble");
  return res.text();
}

export async function fetchDefaultTranscribePrompt(): Promise<string> {
  const res = await fetch(`${API_BASE}/preamble/transcribe-prompt/default`);
  if (!res.ok) throw new Error("Failed to fetch default transcribe prompt");
  return res.text();
}

export async function listJobs(): Promise<JobResponse[]> {
  const res = await fetch(`${API_BASE}/jobs`);
  if (!res.ok) throw new Error("Failed to fetch jobs");
  return res.json();
}

export async function createJob(
  files: File[],
  config: {
    model?: string;
    api_key?: string;
    api_base?: string;
    max_retries?: number;
    dpi?: number;
    preamble?: string;
    transcribe_prompt?: string;
  },
): Promise<JobResponse> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  form.append("config", JSON.stringify(config));

  const res = await fetch(`${API_BASE}/jobs`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to create job");
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch job");
  return res.json();
}

export async function fetchTexSource(jobId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/download/output.tex`);
  if (!res.ok) throw new Error("Failed to fetch .tex source");
  return res.text();
}

export async function getJobPages(jobId: string): Promise<PagesResponse> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/pages`);
  if (!res.ok) throw new Error("Failed to fetch page info");
  return res.json();
}

export function subscribeToJob(
  jobId: string,
  onEvent: (event: ProgressEvent) => void,
  onDone?: () => void,
  onError?: (err: Error) => void,
): () => void {
  const source = new EventSource(`${API_BASE}/jobs/${jobId}/events`);

  const handler = (e: MessageEvent) => {
    const data: ProgressEvent = JSON.parse(e.data);
    onEvent(data);
    if (
      data.event_type === "job_completed" ||
      data.event_type === "job_failed"
    ) {
      source.close();
      onDone?.();
    }
  };

  for (const type of EVENT_TYPES) {
    source.addEventListener(type, handler);
  }

  source.onerror = () => {
    source.close();
    onError?.(new Error("SSE connection lost"));
  };

  return () => source.close();
}

export function downloadUrl(
  jobId: string,
  filename: string,
  forceDownload = false,
): string {
  const base = `${API_BASE}/jobs/${jobId}/download/${filename}`;
  return forceDownload ? `${base}?download=true` : base;
}

export async function getPageLatex(
  jobId: string,
  pageNumber: number,
): Promise<{ job_id: string; page_number: number; latex: string }> {
  const res = await fetch(
    `${API_BASE}/jobs/${jobId}/pages/${pageNumber}/latex`,
  );
  if (!res.ok) throw new Error("Failed to fetch page LaTeX");
  return res.json();
}

export function pageImageUrl(jobId: string, pageNumber: number): string {
  return `${API_BASE}/jobs/${jobId}/pages/${pageNumber}/image`;
}
