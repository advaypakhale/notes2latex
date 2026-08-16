import { Link } from "react-router-dom";
import {
  ArchiveIcon,
  DownloadIcon,
  FileIcon,
  FileTextIcon,
  TriangleAlertIcon,
} from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LatexSource } from "@/components/job/latex-source";
import { PageReview } from "@/components/job/page-review";
import { downloadUrl } from "@/api/client";
import { cn } from "@/lib/utils";
import type { Job } from "@/api/schemas";

function DownloadLink({
  jobId,
  filename,
  children,
}: {
  jobId: string;
  filename: string;
  children: React.ReactNode;
}) {
  return (
    <a
      href={downloadUrl(jobId, filename, true)}
      className={cn(
        buttonVariants({ variant: "outline", size: "lg" }),
        "w-full justify-start gap-2",
      )}
    >
      {children}
      <DownloadIcon className="ml-auto" />
    </a>
  );
}

export function JobResult({ job }: { job: Job }) {
  return (
    <div className="space-y-6">
      {job.has_pdf ? (
        <Card className="py-0">
          <CardContent className="px-0">
            <iframe
              src={downloadUrl(job.job_id, "output.pdf")}
              className="h-[70vh] w-full"
              title="PDF preview"
            />
          </CardContent>
        </Card>
      ) : (
        job.has_tex && (
          <Card>
            <CardContent className="flex items-center gap-2 text-sm text-muted-foreground">
              <TriangleAlertIcon className="size-4 shrink-0" />
              PDF compilation failed. The .tex source was saved, so you can
              download it and compile manually.
            </CardContent>
          </Card>
        )
      )}

      <Tabs defaultValue="review">
        <TabsList>
          <TabsTrigger value="review">Review</TabsTrigger>
          <TabsTrigger value="downloads">Downloads</TabsTrigger>
          {job.has_tex && (
            <TabsTrigger value="source">LaTeX Source</TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="review" keepMounted>
          <PageReview jobId={job.job_id} />
        </TabsContent>

        <TabsContent value="downloads">
          <Card>
            <CardContent className="grid gap-3">
              {job.has_pdf && (
                <DownloadLink jobId={job.job_id} filename="output.pdf">
                  <FileIcon />
                  Download PDF
                </DownloadLink>
              )}
              {job.has_tex && (
                <DownloadLink jobId={job.job_id} filename="output.tex">
                  <FileTextIcon />
                  Download .tex Source
                </DownloadLink>
              )}
              <DownloadLink jobId={job.job_id} filename="all.zip">
                <ArchiveIcon />
                Download All (.zip)
              </DownloadLink>
            </CardContent>
          </Card>
        </TabsContent>

        {job.has_tex && (
          <TabsContent value="source">
            <Card>
              <CardContent>
                <LatexSource jobId={job.job_id} />
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      <Link to="/" className={cn(buttonVariants({ size: "lg" }), "w-full")}>
        Convert Another
      </Link>
    </div>
  );
}
