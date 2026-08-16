import { cn } from "@/lib/utils";

export function CodeBlock({
  className,
  ...props
}: React.ComponentProps<"pre">) {
  return (
    <pre
      className={cn(
        "overflow-auto rounded-lg bg-muted p-4 font-mono text-xs whitespace-pre-wrap",
        className,
      )}
      {...props}
    />
  );
}
