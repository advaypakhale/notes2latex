import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from "@/components/ui/progress";
import { Spinner } from "@/components/ui/spinner";
import type { Job } from "@/api/schemas";

const pageVerbs = {
  transcribing: "Transcribing",
  compiling: "Compiling",
  fixing: "Fixing",
};

function describe(job: Job): string {
  if (!job.phase) return "Starting";
  if (job.phase === "finalizing") return "Assembling document";
  return `${pageVerbs[job.phase]} page ${job.current_page} of ${job.total_pages}`;
}

export function JobProgress({ job }: { job: Job }) {
  // The page named by `current_page` is still being worked on, so it does not
  // count towards the bar until the job moves past it.
  const finished =
    job.phase === "finalizing"
      ? job.total_pages
      : Math.max(job.current_page - 1, 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Spinner className="size-5" />
          Converting
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Progress
          value={job.total_pages > 0 ? finished : null}
          max={job.total_pages || undefined}
        >
          <ProgressLabel className="truncate font-normal text-muted-foreground">
            {describe(job)}
          </ProgressLabel>
          <ProgressValue />
        </Progress>
      </CardContent>
    </Card>
  );
}
