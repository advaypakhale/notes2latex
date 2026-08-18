import type { FallbackProps } from "react-error-boundary";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";

export function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  return (
    <div className="container mx-auto max-w-2xl px-4 py-16">
      <EmptyState
        title="Something went wrong"
        description={error instanceof Error ? error.message : String(error)}
      >
        <Button variant="outline" onClick={resetErrorBoundary}>
          Try again
        </Button>
      </EmptyState>
    </div>
  );
}
