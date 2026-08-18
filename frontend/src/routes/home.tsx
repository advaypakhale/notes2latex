import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ClockIcon, FileTextIcon, XIcon } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FieldError } from "@/components/ui/field";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { EmptyState } from "@/components/empty-state";
import { FileDropzone } from "@/components/file-dropzone";
import { JobStatusBadge } from "@/components/job-status-badge";
import { DeleteJobButton } from "@/components/job/delete-job-button";
import { jobListQuery, useCreateJob } from "@/api/queries";
import { uploadFilesSchema } from "@/api/schemas";
import { toJobConfig, useSettings } from "@/stores/settings";

const recentJobCount = 10;

function formatDate(date: string | null): string {
  if (!date) return "";
  return new Date(date).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function Home() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const jobs = useQuery(jobListQuery(recentJobCount));
  const createJob = useCreateJob();

  const upload = uploadFilesSchema.safeParse(files);

  const submit = () => {
    createJob.mutate(
      { files, config: toJobConfig(useSettings.getState()) },
      {
        onSuccess: (job) => navigate(`/jobs/${job.job_id}`),
        onError: (error) => toast.error(error.message),
      },
    );
  };

  return (
    <div className="container mx-auto max-w-4xl space-y-8 px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle>Convert Notes</CardTitle>
          <CardDescription>
            Upload a PDF or images of your handwritten notes to convert them to
            LaTeX.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <FileDropzone
            onAccepted={(accepted) =>
              setFiles((current) => [...current, ...accepted])
            }
          />

          {files.map((file, index) => (
            <div
              key={`${file.name}-${index}`}
              className="flex items-center gap-2 rounded-md bg-muted px-3 py-2 text-sm"
            >
              <FileTextIcon className="size-4 shrink-0" />
              <span className="flex-1 truncate">{file.name}</span>
              <Button
                variant="ghost"
                size="icon-xs"
                aria-label={`Remove ${file.name}`}
                onClick={() =>
                  setFiles((current) => current.filter((_, i) => i !== index))
                }
              >
                <XIcon />
              </Button>
            </div>
          ))}

          {files.length > 0 && !upload.success && (
            <FieldError errors={upload.error.issues} />
          )}

          <Button
            className="w-full"
            size="lg"
            disabled={!upload.success || createJob.isPending}
            onClick={submit}
          >
            {createJob.isPending ? (
              <>
                <Spinner />
                Starting conversion...
              </>
            ) : (
              "Convert to LaTeX"
            )}
          </Button>
        </CardContent>
      </Card>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Recent Conversions</h2>
        {jobs.isPending ? (
          <Spinner className="text-muted-foreground" />
        ) : jobs.isError ? (
          <EmptyState
            title="Could not load recent conversions"
            description={jobs.error.message}
          />
        ) : jobs.data.length === 0 ? (
          <EmptyState title="Nothing converted yet" />
        ) : (
          jobs.data.map((job) => (
            <Card
              key={job.job_id}
              size="sm"
              className="relative transition-colors hover:bg-muted/50"
            >
              <CardContent className="flex items-center gap-4">
                <div className="min-w-0 flex-1">
                  {/* A button nested in an anchor is invalid markup, so the link
                      covers the card with an overlay rather than wrapping it. */}
                  <Link
                    to={`/jobs/${job.job_id}`}
                    className="block truncate text-sm font-medium after:absolute after:inset-0"
                  >
                    {job.input_filenames.join(", ")}
                  </Link>
                  <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                    <ClockIcon className="size-3" />
                    {formatDate(job.created_at)}
                    {job.total_pages > 0 && (
                      <>
                        <Separator orientation="vertical" className="h-3" />
                        {job.total_pages} page
                        {job.total_pages === 1 ? "" : "s"}
                      </>
                    )}
                  </div>
                </div>
                <div className="relative flex items-center gap-2">
                  <JobStatusBadge status={job.status} />
                  <DeleteJobButton jobId={job.job_id} />
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </section>
    </div>
  );
}
