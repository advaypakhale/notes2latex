import { CircleCheckIcon, TriangleAlertIcon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import type { JobStatus } from "@/api/schemas";

export function JobStatusBadge({ status }: { status: JobStatus }) {
  switch (status) {
    case "completed":
      return (
        <Badge variant="success">
          <CircleCheckIcon />
          Completed
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="destructive">
          <TriangleAlertIcon />
          Failed
        </Badge>
      );
    case "pending":
    case "processing":
      return (
        <Badge variant="secondary">
          <Spinner />
          Processing
        </Badge>
      );
  }
}
