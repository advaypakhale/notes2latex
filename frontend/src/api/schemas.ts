import { z } from "zod";

const jobStatusSchema = z.enum([
  "pending",
  "processing",
  "completed",
  "failed",
]);

const jobPhaseSchema = z.enum([
  "transcribing",
  "compiling",
  "fixing",
  "finalizing",
]);

export const jobSchema = z.object({
  job_id: z.string(),
  status: jobStatusSchema,
  phase: jobPhaseSchema.nullable(),
  model: z.string(),
  current_page: z.number(),
  total_pages: z.number(),
  created_at: z.string().nullable(),
  completed_at: z.string().nullable(),
  error_message: z.string().nullable(),
  input_filenames: z.array(z.string()),
  has_pdf: z.boolean(),
  has_tex: z.boolean(),
});

export const jobListSchema = z.array(jobSchema);

export const jobPagesSchema = z.object({ total_pages: z.number() });

export const pageLatexSchema = z.object({
  job_id: z.string(),
  page_number: z.number(),
  latex: z.string(),
});

export const jobConfigSchema = z.object({
  model: z.string().min(1).optional(),
  api_key: z.string().min(1).optional(),
  preamble: z.string().min(1).optional(),
});

/** Also passed straight to react-dropzone as its `accept` map. */
export const acceptedFileTypes = {
  "application/pdf": [".pdf"],
  "image/png": [".png"],
  "image/jpeg": [".jpg", ".jpeg"],
};

export const maxUploadFiles = 20;

const acceptedMimeTypes: string[] = Object.keys(acceptedFileTypes);

export const uploadFilesSchema = z
  .array(
    z
      .instanceof(File)
      .refine(
        (file) => acceptedMimeTypes.includes(file.type),
        "Only PDF, PNG and JPG files can be converted",
      ),
  )
  .min(1, "Add at least one file")
  .max(maxUploadFiles, `Add at most ${maxUploadFiles} files`);

export type JobStatus = z.infer<typeof jobStatusSchema>;
export type Job = z.infer<typeof jobSchema>;
export type JobConfig = z.infer<typeof jobConfigSchema>;
