import { useEffect } from "react";
import { preload } from "react-dom";
import {
  queryOptions,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import * as api from "./client";
import type { JobStatus } from "./schemas";

const runningPollMs = 1000;

const isRunning = (status: JobStatus | undefined) =>
  status === "pending" || status === "processing";

export const jobKeys = {
  lists: ["jobs", "list"] as const,
  list: (limit: number) => ["jobs", "list", { limit }] as const,
  detail: (jobId: string) => ["jobs", "detail", jobId] as const,
  pages: (jobId: string) => ["jobs", "detail", jobId, "pages"] as const,
  pageLatex: (jobId: string, page: number) =>
    ["jobs", "detail", jobId, "pages", page, "latex"] as const,
  tex: (jobId: string) => ["jobs", "detail", jobId, "tex"] as const,
};

export const jobListQuery = (limit: number) =>
  queryOptions({
    queryKey: jobKeys.list(limit),
    queryFn: () => api.listJobs(limit),
    refetchInterval: ({ state }) =>
      state.data?.some((job) => isRunning(job.status)) ? runningPollMs : false,
  });

export const jobQuery = (jobId: string) =>
  queryOptions({
    queryKey: jobKeys.detail(jobId),
    queryFn: () => api.getJob(jobId),
    refetchInterval: ({ state }) =>
      isRunning(state.data?.status) ? runningPollMs : false,
    // A finished job never changes again.
    staleTime: ({ state }) => (isRunning(state.data?.status) ? 0 : Infinity),
  });

export const jobPagesQuery = (jobId: string) =>
  queryOptions({
    queryKey: jobKeys.pages(jobId),
    queryFn: () => api.getJobPages(jobId),
    staleTime: Infinity,
  });

export const texSourceQuery = (jobId: string) =>
  queryOptions({
    queryKey: jobKeys.tex(jobId),
    queryFn: () => api.getTexSource(jobId),
    staleTime: Infinity,
  });

export const defaultPreambleQuery = queryOptions({
  queryKey: ["preamble", "default"],
  queryFn: api.getDefaultPreamble,
  staleTime: Infinity,
});

const pageLatexQuery = (jobId: string, page: number) =>
  queryOptions({
    queryKey: jobKeys.pageLatex(jobId, page),
    queryFn: () => api.getPageLatex(jobId, page),
    staleTime: Infinity,
  });

/** Loads one page's LaTeX and warms the neighbouring pages for quick paging. */
export function usePageLatex(jobId: string, page: number, totalPages: number) {
  const queryClient = useQueryClient();

  useEffect(() => {
    for (const neighbour of [page - 1, page + 1]) {
      if (neighbour >= 1 && neighbour <= totalPages) {
        queryClient.prefetchQuery(pageLatexQuery(jobId, neighbour));
        preload(api.pageImageUrl(jobId, neighbour), { as: "image" });
      }
    }
  }, [queryClient, jobId, page, totalPages]);

  return useQuery({ ...pageLatexQuery(jobId, page), enabled: totalPages > 0 });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createJob,
    onSuccess: (job) => {
      queryClient.setQueryData(jobKeys.detail(job.job_id), job);
      queryClient.invalidateQueries({ queryKey: jobKeys.lists });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.deleteJob,
    onSuccess: (_, jobId) => {
      queryClient.removeQueries({ queryKey: jobKeys.detail(jobId) });
      queryClient.invalidateQueries({ queryKey: jobKeys.lists });
    },
  });
}
