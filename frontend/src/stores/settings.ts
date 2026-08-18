import { z } from "zod";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { JobConfig } from "@/api/schemas";

const settingsSchema = z.object({
  model: z.string().default("openrouter/google/gemini-3-flash-preview"),
  customModel: z.string().default(""),
  useCustomModel: z.boolean().default(false),
  apiKey: z.string().default(""),
  /** Empty means "let the server use its own preamble". */
  preamble: z.string().default(""),
});

type Settings = z.infer<typeof settingsSchema>;

type SettingsStore = Settings & {
  update: (patch: Partial<Settings>) => void;
};

export const useSettings = create<SettingsStore>()(
  persist(
    (set) => ({
      ...settingsSchema.parse({}),
      update: (patch) => set(patch),
    }),
    {
      name: "n2l_settings",
      merge: (persisted, current) => ({
        ...current,
        ...settingsSchema.safeParse(persisted).data,
      }),
    },
  ),
);

/** Blank fields are omitted so the server falls back to its own defaults. */
export function toJobConfig(settings: Settings): JobConfig {
  const model = settings.useCustomModel ? settings.customModel : settings.model;
  return {
    model: model || undefined,
    api_key: settings.apiKey || undefined,
    preamble: settings.preamble || undefined,
  };
}
