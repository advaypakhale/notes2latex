import { Link } from "react-router-dom";
import { ArrowLeftIcon } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function BackLink({ className }: { className?: string }) {
  return (
    <Link
      to="/"
      className={cn(
        buttonVariants({ variant: "ghost", size: "sm" }),
        "mb-6 -ml-2",
        className,
      )}
    >
      <ArrowLeftIcon />
      Back
    </Link>
  );
}
