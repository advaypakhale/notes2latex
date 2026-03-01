import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  Loader2,
  AlertCircle,
  Download,
  FileText,
  File,
  Archive,
  ArrowLeft,
  Copy,
  Check,
  ChevronLeft,
  ChevronRight,
  Filter,
  FilterX,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  subscribeToJob,
  getJob,
  fetchTexSource,
  downloadUrl,
  getJobPages,
  getPageLatex,
  pageImageUrl,
} from "@/lib/api";
import type { ProgressEvent, JobResponse } from "@/lib/types";

function humanStatus(event: ProgressEvent): string {
  switch (event.event_type) {
    case "job_started":
      return `Starting conversion of ${event.total_pages} page${event.total_pages !== 1 ? "s" : ""}...`;
    case "page_generating":
      return `Transcribing page ${event.page} of ${event.total_pages}...`;
    case "page_compiling":
      return `Compiling page ${event.page} of ${event.total_pages}...`;
    case "page_compiled_ok":
      return `Page ${event.page} compiled successfully`;
    case "page_fix_attempt":
      return `Fixing compilation errors on page ${event.page} (attempt ${event.retry} of ${event.max_retries})...`;
    case "page_done":
      return `Page ${event.page} of ${event.total_pages} done`;
    case "finalizing":
      return "Assembling final document...";
    case "job_completed":
      return "Conversion complete";
    case "job_failed":
      return event.message || "Conversion failed";
    default:
      return event.message || "Processing...";
  }
}

function ProcessingView({
  latestEvent,
}: {
  latestEvent: ProgressEvent | null;
}) {
  const totalPages = latestEvent?.total_pages ?? 0;
  const currentPage = latestEvent?.page ?? 0;
  // Count completed pages (page_done events advance this)
  const progressPercent =
    totalPages > 0 ? Math.round((currentPage / totalPages) * 100) : 0;
  const statusText = latestEvent ? humanStatus(latestEvent) : "Connecting...";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="h-5 w-5 animate-spin" />
          Converting
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{statusText}</span>
            {totalPages > 0 && (
              <span className="font-medium">{progressPercent}%</span>
            )}
          </div>
          <Progress value={progressPercent} />
        </div>
      </CardContent>
    </Card>
  );
}

function ReviewTab({ jobId }: { jobId: string }) {
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageLatex, setPageLatex] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Fetch page count on mount
  useEffect(() => {
    getJobPages(jobId)
      .then((data) => {
        setTotalPages(data.total_pages);
      })
      .catch(() => setTotalPages(0));
  }, [jobId]);

  // Fetch LaTeX for current page
  useEffect(() => {
    if (totalPages === 0) return;
    let cancelled = false;
    getPageLatex(jobId, currentPage)
      .then((data) => {
        if (!cancelled) setPageLatex(data.latex);
      })
      .catch(() => {
        if (!cancelled) setPageLatex("Failed to load LaTeX for this page.");
      });
    return () => {
      cancelled = true;
    };
  }, [jobId, currentPage, totalPages]);

  const copyPageLatex = async () => {
    if (!pageLatex) return;
    await navigator.clipboard.writeText(pageLatex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (totalPages === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          No page data available for review.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Page navigation */}
      <div className="flex items-center justify-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage <= 1}
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>
        <span className="text-sm font-medium min-w-[120px] text-center">
          Page {currentPage} of {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          disabled={currentPage >= totalPages}
        >
          Next
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Side-by-side layout: stacks vertically on narrow screens */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Original page image */}
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Original (Page {currentPage})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-2">
            <div className="overflow-auto max-h-[70vh] rounded border bg-muted/30">
              <img
                src={pageImageUrl(jobId, currentPage)}
                alt={`Original page ${currentPage}`}
                className="w-full h-auto"
              />
            </div>
          </CardContent>
        </Card>

        {/* Right: Generated LaTeX for this page */}
        <Card>
          <CardHeader className="py-3 px-4 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Generated LaTeX (Page {currentPage})
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={copyPageLatex}
              disabled={!pageLatex}
            >
              {copied ? (
                <>
                  <Check className="mr-1 h-3 w-3" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="mr-1 h-3 w-3" />
                  Copy
                </>
              )}
            </Button>
          </CardHeader>
          <CardContent className="p-2">
            {!pageLatex ? (
              <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Loading...
              </div>
            ) : (
              <pre className="text-xs bg-muted rounded-md p-4 overflow-auto max-h-[70vh] whitespace-pre-wrap font-mono">
                {pageLatex}
              </pre>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/**
 * Split LaTeX source into segments by page markers.
 * Content before the first marker (preamble) gets page_number = 0.
 */
function splitByPageMarkers(
  tex: string,
): { page_number: number; content: string }[] {
  const segments: { page_number: number; content: string }[] = [];
  const lines = tex.split("\n");
  let currentPage = 0;
  let currentLines: string[] = [];

  for (const line of lines) {
    const match = line.match(/^% ====== Page (\d+) ======$/);
    if (match) {
      if (currentLines.length > 0) {
        segments.push({
          page_number: currentPage,
          content: currentLines.join("\n"),
        });
      }
      currentPage = parseInt(match[1], 10);
      currentLines = [line];
    } else {
      currentLines.push(line);
    }
  }
  if (currentLines.length > 0) {
    segments.push({
      page_number: currentPage,
      content: currentLines.join("\n"),
    });
  }

  return segments;
}

function LatexSourceView({
  texSource,
  texLoading,
}: {
  texSource: string | null;
  texLoading: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const [filterPage, setFilterPage] = useState<number | null>(null);
  const preRef = useRef<HTMLPreElement>(null);

  const segments = useMemo(
    () => (texSource ? splitByPageMarkers(texSource) : []),
    [texSource],
  );

  const pageNumbers = useMemo(
    () => segments.filter((s) => s.page_number > 0).map((s) => s.page_number),
    [segments],
  );

  const copyTex = async () => {
    if (!texSource) return;
    await navigator.clipboard.writeText(texSource);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const scrollToPage = (pageNum: number) => {
    if (!preRef.current) return;
    setFilterPage(null);
    requestAnimationFrame(() => {
      const marker = preRef.current?.querySelector(`[data-page="${pageNum}"]`);
      if (marker) {
        marker.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  };

  const toggleFilter = (pageNum: number) => {
    setFilterPage((prev) => (prev === pageNum ? null : pageNum));
  };

  const displayedSegments = useMemo(() => {
    if (filterPage === null) return segments;
    return segments.filter(
      (s) => s.page_number === 0 || s.page_number === filterPage,
    );
  }, [segments, filterPage]);

  if (texLoading) {
    return <p className="text-sm text-muted-foreground">Loading...</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          {pageNumbers.length > 0 && (
            <>
              <span className="text-xs text-muted-foreground mr-1">Pages:</span>
              {pageNumbers.map((p) => (
                <Button
                  key={p}
                  variant={filterPage === p ? "default" : "outline"}
                  size="sm"
                  className="h-7 w-7 p-0 text-xs"
                  onClick={() => scrollToPage(p)}
                  onDoubleClick={() => toggleFilter(p)}
                  title={`Click to scroll to page ${p}, double-click to filter`}
                >
                  {p}
                </Button>
              ))}
              {filterPage !== null && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs ml-1"
                  onClick={() => setFilterPage(null)}
                >
                  <FilterX className="h-3 w-3 mr-1" />
                  Show all
                </Button>
              )}
            </>
          )}
        </div>
        <div className="flex items-center gap-2">
          {filterPage !== null && (
            <Badge variant="secondary" className="text-xs">
              <Filter className="h-3 w-3 mr-1" />
              Page {filterPage} only
            </Badge>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={copyTex}
            disabled={!texSource}
          >
            {copied ? (
              <>
                <Check className="mr-2 h-3 w-3" />
                Copied
              </>
            ) : (
              <>
                <Copy className="mr-2 h-3 w-3" />
                Copy
              </>
            )}
          </Button>
        </div>
      </div>

      <pre
        ref={preRef}
        className="text-xs bg-muted rounded-md p-4 overflow-auto max-h-[60vh] whitespace-pre-wrap"
      >
        {displayedSegments.map((segment, idx) => {
          const newlinePos = segment.content.indexOf("\n");
          const markerLine =
            newlinePos >= 0
              ? segment.content.slice(0, newlinePos)
              : segment.content;
          const bodyContent =
            newlinePos >= 0 ? segment.content.slice(newlinePos + 1) : "";

          return (
            <span key={`${segment.page_number}-${idx}`}>
              {segment.page_number > 0 ? (
                <>
                  <span
                    data-page={segment.page_number}
                    className="block bg-primary/10 text-primary font-semibold border-l-2 border-primary pl-2 -ml-2 my-2 py-0.5"
                  >
                    {markerLine}
                  </span>
                  {bodyContent}
                </>
              ) : (
                segment.content
              )}
              {idx < displayedSegments.length - 1 ? "\n" : ""}
            </span>
          );
        })}
      </pre>
    </div>
  );
}

function ResultView({ job }: { job: JobResponse }) {
  const [texSource, setTexSource] = useState<string | null>(null);
  const [texLoading, setTexLoading] = useState(false);

  const loadTex = useCallback(() => {
    if (texSource !== null || texLoading || !job.has_tex) return;
    setTexLoading(true);
    fetchTexSource(job.job_id)
      .then(setTexSource)
      .catch(() => setTexSource("Failed to load source."))
      .finally(() => setTexLoading(false));
  }, [job.job_id, job.has_tex, texSource, texLoading]);

  return (
    <div className="space-y-6">
      {/* PDF preview */}
      {job.has_pdf && (
        <Card>
          <CardContent className="p-0">
            <iframe
              src={downloadUrl(job.job_id, "output.pdf")}
              className="w-full rounded-lg"
              style={{ height: "70vh" }}
              title="PDF Preview"
            />
          </CardContent>
        </Card>
      )}

      {!job.has_pdf && job.has_tex && (
        <Card>
          <CardContent className="py-4">
            <p className="text-sm text-yellow-600">
              PDF compilation failed, but the .tex source was saved. You can
              download it and compile manually.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Tabs: Review / Downloads / LaTeX Source */}
      <Tabs
        defaultValue="review"
        onValueChange={(v) => {
          if (v === "source") loadTex();
        }}
      >
        <TabsList>
          <TabsTrigger value="review">Review</TabsTrigger>
          <TabsTrigger value="downloads">Downloads</TabsTrigger>
          {job.has_tex && (
            <TabsTrigger value="source">LaTeX Source</TabsTrigger>
          )}
        </TabsList>

        <TabsContent value="review">
          <ReviewTab jobId={job.job_id} />
        </TabsContent>

        <TabsContent value="downloads">
          <Card>
            <CardContent className="py-4">
              <div className="grid gap-3">
                {job.has_pdf && (
                  <a href={downloadUrl(job.job_id, "output.pdf", true)}>
                    <Button
                      variant="outline"
                      className="w-full justify-start gap-2"
                    >
                      <File className="h-4 w-4" />
                      Download PDF
                      <Download className="h-4 w-4 ml-auto" />
                    </Button>
                  </a>
                )}
                {job.has_tex && (
                  <a href={downloadUrl(job.job_id, "output.tex", true)}>
                    <Button
                      variant="outline"
                      className="w-full justify-start gap-2"
                    >
                      <FileText className="h-4 w-4" />
                      Download .tex Source
                      <Download className="h-4 w-4 ml-auto" />
                    </Button>
                  </a>
                )}
                <a href={downloadUrl(job.job_id, "all.zip", true)}>
                  <Button
                    variant="outline"
                    className="w-full justify-start gap-2"
                  >
                    <Archive className="h-4 w-4" />
                    Download All (.zip)
                    <Download className="h-4 w-4 ml-auto" />
                  </Button>
                </a>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {job.has_tex && (
          <TabsContent value="source">
            <Card>
              <CardContent className="py-4">
                <LatexSourceView
                  texSource={texSource}
                  texLoading={texLoading}
                />
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      <Button asChild className="w-full">
        <Link to="/">Convert Another</Link>
      </Button>
    </div>
  );
}

function FailedView({ errorMessage }: { errorMessage: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-5 w-5" />
          Conversion Failed
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{errorMessage}</p>
        <Button asChild>
          <Link to="/">Try Again</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

export function JobPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<JobResponse | null>(null);
  const [latestEvent, setLatestEvent] = useState<ProgressEvent | null>(null);
  const [status, setStatus] = useState<
    "loading" | "processing" | "completed" | "failed"
  >("loading");
  const [errorMessage, setErrorMessage] = useState("");
  const unsubRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!id) return;

    // Fetch initial job state
    getJob(id)
      .then((j) => {
        setJob(j);
        if (j.status === "completed") {
          setStatus("completed");
          return;
        }
        if (j.status === "failed") {
          setStatus("failed");
          setErrorMessage(j.error_message ?? "Unknown error");
          return;
        }

        // Job is pending/processing — connect SSE (replays all past events)
        setStatus("processing");
        const unsub = subscribeToJob(
          id,
          (event: ProgressEvent) => {
            setLatestEvent(event);
            if (event.event_type === "job_completed") {
              // Refetch job to get has_pdf/has_tex
              getJob(id).then((updated) => {
                setJob(updated);
                setStatus("completed");
              });
            } else if (event.event_type === "job_failed") {
              setStatus("failed");
              setErrorMessage(event.message);
            }
          },
          undefined,
          () => {
            // SSE error — job might have finished while we were away
            getJob(id).then((j) => {
              setJob(j);
              if (j.status === "completed") setStatus("completed");
              else if (j.status === "failed") {
                setStatus("failed");
                setErrorMessage(j.error_message ?? "Unknown error");
              }
              // If still processing but SSE is gone (server restart), show last known state
            });
          },
        );
        unsubRef.current = unsub;
      })
      .catch(() => {
        navigate("/");
      });

    return () => {
      unsubRef.current?.();
    };
  }, [id, navigate]);

  if (status === "loading") {
    return (
      <div className="container mx-auto max-w-4xl py-8 px-4 text-center text-muted-foreground">
        Loading...
      </div>
    );
  }

  return (
    <div
      className={`container mx-auto py-8 px-4 ${status === "completed" ? "max-w-7xl" : "max-w-4xl"}`}
    >
      <Button variant="ghost" size="sm" className="mb-6 -ml-2" asChild>
        <Link to="/">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Link>
      </Button>

      {status === "processing" && <ProcessingView latestEvent={latestEvent} />}
      {status === "completed" && job && <ResultView job={job} />}
      {status === "failed" && <FailedView errorMessage={errorMessage} />}
    </div>
  );
}
