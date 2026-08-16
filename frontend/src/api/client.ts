import { z } from "zod";
import {
  jobConfigSchema,
  jobListSchema,
  jobPagesSchema,
  jobSchema,
  pageLatexSchema,
  uploadFilesSchema,
  type JobConfig,
} from "./schemas";

export const apiBase = "/api/v1";

const errorBodySchema = z.object({ detail: z.string() });

async function failure(res: Response): Promise<Error> {
  const body = errorBodySchema.safeParse(await res.json().catch(() => null));
  return new Error(body.success ? body.data.detail : res.statusText);
}

async function get<T extends z.ZodType>(
  path: string,
  schema: T,
): Promise<z.infer<T>> {
  const res = await fetch(`${apiBase}${path}`);
  if (!res.ok) throw await failure(res);
  return schema.parse(await res.json());
}

async function getText(path: string): Promise<string> {
  const res = await fetch(`${apiBase}${path}`);
  if (!res.ok) throw await failure(res);
  return res.text();
}

export const listJobs = (limit: number) =>
  get(`/jobs?limit=${limit}`, jobListSchema);

export const getJob = (jobId: string) => get(`/jobs/${jobId}`, jobSchema);

export const getJobPages = (jobId: string) =>
  get(`/jobs/${jobId}/pages`, jobPagesSchema);

export const getPageLatex = (jobId: string, page: number) =>
  get(`/jobs/${jobId}/pages/${page}/latex`, pageLatexSchema);

export const getTexSource = (jobId: string) =>
  getText(`/jobs/${jobId}/download/output.tex`);

export const getDefaultPreamble = () => getText("/preamble/default");

export async function createJob(input: { files: File[]; config: JobConfig }) {
  const files = uploadFilesSchema.parse(input.files);
  const config = jobConfigSchema.parse(input.config);

  const form = new FormData();
  for (const file of files) form.append("files", file);
  form.append("config", JSON.stringify(config));

  const res = await fetch(`${apiBase}/jobs`, { method: "POST", body: form });
  if (!res.ok) throw await failure(res);
  return jobSchema.parse(await res.json());
}

export async function deleteJob(jobId: string): Promise<void> {
  const res = await fetch(`${apiBase}/jobs/${jobId}`, { method: "DELETE" });
  // A job that is already gone is the result the caller asked for.
  if (!res.ok && res.status !== 404) throw await failure(res);
}

export const pageImageUrl = (jobId: string, page: number) =>
  `${apiBase}/jobs/${jobId}/pages/${page}/image`;

export const downloadUrl = (
  jobId: string,
  filename: string,
  forceDownload = false,
) =>
  `${apiBase}/jobs/${jobId}/download/${filename}${forceDownload ? "?download=true" : ""}`;
