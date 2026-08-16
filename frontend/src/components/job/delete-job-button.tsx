import { useState } from "react";
import { Trash2Icon } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { useDeleteJob } from "@/api/queries";

export function DeleteJobButton({
  jobId,
  onDeleted,
}: {
  jobId: string;
  onDeleted?: () => void;
}) {
  const [open, setOpen] = useState(false);
  const deleteJob = useDeleteJob();

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger
        render={
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Delete conversion"
          />
        }
      >
        <Trash2Icon />
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this conversion?</AlertDialogTitle>
          <AlertDialogDescription>
            The PDF and .tex source go with it. This cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            variant="destructive"
            disabled={deleteJob.isPending}
            onClick={() =>
              deleteJob.mutate(jobId, {
                onSuccess: () => {
                  setOpen(false);
                  onDeleted?.();
                },
                onError: (error) => toast.error(error.message),
              })
            }
          >
            {deleteJob.isPending && <Spinner />}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
