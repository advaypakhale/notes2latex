import { useDropzone } from "react-dropzone";
import { UploadIcon } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { acceptedFileTypes, maxUploadFiles } from "@/api/schemas";

export function FileDropzone({
  onAccepted,
}: {
  onAccepted: (files: File[]) => void;
}) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: acceptedFileTypes,
    maxFiles: maxUploadFiles,
    onDropAccepted: onAccepted,
    onDropRejected: (rejections) =>
      toast.error(
        rejections[0]?.errors[0]?.message ?? "Those files can't be converted",
      ),
  });

  return (
    <div
      {...getRootProps({
        className: cn(
          "cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50",
        ),
      })}
    >
      <input {...getInputProps()} />
      <UploadIcon className="mx-auto mb-3 size-10 text-muted-foreground" />
      <p className="text-sm text-muted-foreground">
        Drop PDF, PNG, or JPG files here, or click to browse
      </p>
    </div>
  );
}
