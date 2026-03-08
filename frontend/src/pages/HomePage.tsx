import { useState, useCallback, useEffect, type DragEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Upload,
  X,
  FileText,
  Loader2,
  Clock,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { createJob, listJobs } from "@/lib/api";
import { loadSettings, getEffectiveModel } from "@/lib/settings";
import type { JobResponse, JobStatus } from "@/lib/types";

const ACCEPTED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg"];
const ACCEPTED = ACCEPTED_EXTENSIONS.map((e) => `.${e}`).join(",");

function StatusBadge({ status }: { status: JobStatus }) {
  switch (status) {
    case "completed":
      return (
        <Badge
          variant="outline"
          className="text-green-700 border-green-300 bg-green-50"
        >
          <CheckCircle2 className="mr-1 h-3 w-3" />
          Completed
        </Badge>
      );
    case "processing":
    case "pending":
      return (
        <Badge
          variant="outline"
          className="text-blue-700 border-blue-300 bg-blue-50"
        >
          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          Processing
        </Badge>
      );
    case "failed":
      return (
        <Badge
          variant="outline"
          className="text-red-700 border-red-300 bg-red-50"
        >
          <AlertCircle className="mr-1 h-3 w-3" />
          Failed
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function HomePage() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(true);

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch(() => {})
      .finally(() => setLoadingJobs(false));
  }, []);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const arr = Array.from(newFiles).filter((f) => {
      const ext = f.name.toLowerCase().split(".").pop();
      return ACCEPTED_EXTENSIONS.includes(ext ?? "");
    });
    setFiles((prev) => [...prev, ...arr]);
  }, []);

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      addFiles(e.dataTransfer.files);
    },
    [addFiles],
  );

  const removeFile = (idx: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    if (files.length === 0) return;
    setError("");
    setSubmitting(true);

    const settings = loadSettings();
    const model = getEffectiveModel(settings);

    try {
      const res = await createJob(files, {
        model: model || undefined,
        api_key: settings.apiKey || undefined,
        preamble: settings.preamble || undefined,
        max_retries: settings.maxRetries ?? undefined,
        dpi: settings.dpi ?? undefined,
        temperature: settings.temperature ?? undefined,
        max_tokens: settings.maxTokens ?? undefined,
      });
      navigate(`/jobs/${res.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4 space-y-8">
      {/* Upload section */}
      <Card>
        <CardHeader>
          <CardTitle>Convert Notes</CardTitle>
          <CardDescription>
            Upload a PDF or images of your handwritten notes to convert them to
            LaTeX.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              dragOver
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-primary/50"
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => document.getElementById("file-input")?.click()}
          >
            <Upload className="mx-auto h-10 w-10 text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground">
              Drop PDF, PNG, or JPG files here, or click to browse
            </p>
            <input
              id="file-input"
              type="file"
              accept={ACCEPTED}
              multiple
              className="hidden"
              onChange={(e) => e.target.files && addFiles(e.target.files)}
            />
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              {files.map((f, i) => (
                <div
                  key={`${f.name}-${i}`}
                  className="flex items-center gap-2 text-sm bg-muted rounded-md px-3 py-2"
                >
                  <FileText className="h-4 w-4 shrink-0" />
                  <span className="truncate flex-1">{f.name}</span>
                  <button
                    onClick={() => removeFile(i)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <Button
            className="w-full"
            size="lg"
            disabled={files.length === 0 || submitting}
            onClick={handleSubmit}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting conversion...
              </>
            ) : (
              "Convert to LaTeX"
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Recent jobs */}
      {(loadingJobs || jobs.length > 0) && (
        <div>
          <h2 className="text-lg font-semibold mb-4">Recent Conversions</h2>
          {loadingJobs ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : (
            <div className="space-y-2">
              {jobs.map((job) => (
                <Link
                  key={job.job_id}
                  to={`/jobs/${job.job_id}`}
                  className="block"
                >
                  <Card className="hover:bg-muted/50 transition-colors">
                    <CardContent className="flex items-center gap-4 py-3 px-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">
                          {job.input_filenames.join(", ")}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(job.created_at)}
                          {job.total_pages > 0 && (
                            <>
                              <Separator
                                orientation="vertical"
                                className="h-3"
                              />
                              {job.total_pages} page
                              {job.total_pages !== 1 ? "s" : ""}
                            </>
                          )}
                        </div>
                      </div>
                      <StatusBadge status={job.status} />
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
