import { Link } from "react-router-dom";
import { buttonVariants } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";

export function NotFound() {
  return (
    <div className="container mx-auto max-w-2xl px-4 py-16">
      <EmptyState
        title="Page not found"
        description="That address does not match anything in notes2latex."
      >
        <Link to="/" className={buttonVariants({ variant: "outline" })}>
          Back to upload
        </Link>
      </EmptyState>
    </div>
  );
}
