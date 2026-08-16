import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { CodeBlock } from "@/components/code-block";
import { CopyButton } from "@/components/copy-button";
import { EmptyState } from "@/components/empty-state";
import { pageImageUrl } from "@/api/client";
import { jobPagesQuery, usePageLatex } from "@/api/queries";

export function PageReview({ jobId }: { jobId: string }) {
  const [page, setPage] = useState(1);
  const pages = useQuery(jobPagesQuery(jobId));
  const totalPages = pages.data?.total_pages ?? 0;
  const latex = usePageLatex(jobId, page, totalPages);

  if (pages.isPending || totalPages === 0) {
    return (
      <Card>
        <CardContent>
          {pages.isPending ? (
            <div className="flex justify-center py-8">
              <Spinner className="text-muted-foreground" />
            </div>
          ) : (
            <EmptyState
              title="No page data available for review"
              description={pages.error?.message}
            />
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page <= 1}
        >
          <ChevronLeftIcon />
          Previous
        </Button>
        <span className="min-w-30 text-center text-sm font-medium">
          Page {page} of {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
        >
          Next
          <ChevronRightIcon />
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">
              Original (Page {page})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[70vh] overflow-auto rounded-lg border bg-muted/30">
              <img
                src={pageImageUrl(jobId, page)}
                alt={`Original page ${page}`}
                className="h-auto w-full"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-muted-foreground">
              Generated LaTeX (Page {page})
            </CardTitle>
            <CardAction>
              <CopyButton text={latex.data?.latex} />
            </CardAction>
          </CardHeader>
          <CardContent>
            {latex.isPending ? (
              <div className="flex h-40 items-center justify-center gap-2 text-sm text-muted-foreground">
                <Spinner />
                Loading...
              </div>
            ) : latex.isError ? (
              <p className="text-sm text-destructive">{latex.error.message}</p>
            ) : (
              <CodeBlock className="max-h-[70vh]">{latex.data.latex}</CodeBlock>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
