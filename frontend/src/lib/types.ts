export type JobStatus = "pending" | "processing" | "completed" | "failed";

export type EventType =
  | "job_started"
  | "page_generating"
  | "page_compiling"
  | "page_compiled_ok"
  | "page_fix_attempt"
  | "page_done"
  | "finalizing"
  | "job_completed"
  | "job_failed";

export interface ProgressEvent {
  event_type: EventType;
  page: number;
  total_pages: number;
  retry: number;
  max_retries: number;
  message: string;
}

export interface PageInfo {
  page_number: number;
  has_content: boolean;
}

export interface PagesResponse {
  total_pages: number;
  pages: PageInfo[];
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  model: string;
  total_pages: number;
  created_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  input_filenames: string[];
  has_pdf: boolean;
  has_tex: boolean;
}
