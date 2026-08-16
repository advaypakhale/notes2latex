import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Spinner } from "@/components/ui/spinner";
import { BackLink } from "@/components/back-link";
import { EmptyState } from "@/components/empty-state";
import { DeleteJobButton } from "@/components/job/delete-job-button";
import { JobFailed } from "@/components/job/job-failed";
import { JobProgress } from "@/components/job/job-progress";
import { JobResult } from "@/components/job/job-result";
import { jobQuery } from "@/api/queries";
import { cn } from "@/lib/utils";

export function JobDetail() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const job = useQuery(jobQuery(id));

  if (job.isPending) {
    return (
      <div className="container mx-auto flex max-w-4xl justify-center px-4 py-8">
        <Spinner className="size-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "container mx-auto px-4 py-8",
        job.data?.status === "completed" ? "max-w-7xl" : "max-w-4xl",
      )}
    >
      <div className="mb-6 flex items-center justify-between">
        <BackLink className="mb-0" />
        {job.data && (
          <DeleteJobButton
            jobId={job.data.job_id}
            onDeleted={() => navigate("/", { replace: true })}
          />
        )}
      </div>

      {!job.data ? (
        <EmptyState
          title="Could not load this conversion"
          description={job.error?.message}
        />
      ) : job.data.status === "completed" ? (
        <JobResult job={job.data} />
      ) : job.data.status === "failed" ? (
        <JobFailed message={job.data.error_message ?? "Unknown error"} />
      ) : (
        <JobProgress job={job.data} />
      )}
    </div>
  );
}
