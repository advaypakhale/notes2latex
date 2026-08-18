import { useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Spinner } from "@/components/ui/spinner";
import { CodeBlock } from "@/components/code-block";
import { CopyButton } from "@/components/copy-button";
import { texSourceQuery } from "@/api/queries";

/** Marker the backend writes above each page's block in `output.tex`. */
const pageMarker = /(^% ={6} Page (\d+) ={6}$)/m;

const allPages = "all";

type Segment = {
  /** 0 for the preamble, which sits above the first marker. */
  page: number;
  marker: string;
  body: string;
};

function splitByPage(tex: string): Segment[] {
  const [preamble, ...marked] = tex.split(pageMarker);
  const segments: Segment[] = [{ page: 0, marker: "", body: preamble }];

  for (let i = 0; i < marked.length; i += 3) {
    segments.push({
      page: Number(marked[i + 1]),
      marker: marked[i],
      body: (marked[i + 2] ?? "").replace(/^\n/, ""),
    });
  }

  return segments;
}

export function LatexSource({ jobId }: { jobId: string }) {
  const tex = useQuery(texSourceQuery(jobId));
  const [filterPage, setFilterPage] = useState<number | null>(null);
  const source = useRef<HTMLPreElement>(null);

  const { segments, pages, filterItems } = useMemo(() => {
    const segments = splitByPage(tex.data ?? "");
    const pages = segments.slice(1).map((s) => s.page);
    return {
      segments,
      pages,
      filterItems: [
        { value: allPages, label: "All pages" },
        ...pages.map((page) => ({
          value: String(page),
          label: `Page ${page}`,
        })),
      ],
    };
  }, [tex.data]);
  const shown =
    filterPage === null
      ? segments
      : segments.filter((s) => s.page === 0 || s.page === filterPage);

  if (tex.isPending) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Spinner />
        Loading...
      </div>
    );
  }

  if (tex.isError) {
    return <p className="text-sm text-destructive">{tex.error.message}</p>;
  }

  const scrollToPage = (page: number) =>
    source.current
      ?.querySelector(`[data-page="${page}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {filterPage === null && pages.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-xs text-muted-foreground">
              Jump to page:
            </span>
            {pages.map((page) => (
              <Button
                key={page}
                variant="outline"
                size="icon-xs"
                onClick={() => scrollToPage(page)}
                aria-label={`Jump to page ${page}`}
              >
                {page}
              </Button>
            ))}
          </div>
        )}
        <div className="ml-auto flex items-center gap-2">
          {pages.length > 0 && (
            <Select
              items={filterItems}
              value={filterPage === null ? allPages : String(filterPage)}
              onValueChange={(value) =>
                setFilterPage(value === allPages ? null : Number(value))
              }
            >
              <SelectTrigger size="sm" aria-label="Pages to show">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {filterItems.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <CopyButton text={tex.data} />
        </div>
      </div>

      <CodeBlock ref={source} className="max-h-[60vh]">
        {shown.map((segment) => (
          <span key={segment.page}>
            {segment.page > 0 && (
              <span
                data-page={segment.page}
                className="-ml-2 my-2 block border-l-2 border-primary bg-primary/10 py-0.5 pl-2 font-semibold text-primary"
              >
                {segment.marker}
              </span>
            )}
            {segment.body}
          </span>
        ))}
      </CodeBlock>
    </div>
  );
}
