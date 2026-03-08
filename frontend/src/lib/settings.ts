const STORAGE_KEY = "n2l_settings";

export interface AppSettings {
  model: string;
  customModel: string;
  useCustomModel: boolean;
  apiKey: string;
  preamble: string;
  maxRetries: number | null;
  dpi: number | null;
  temperature: number | null;
  maxTokens: number | null;
}

const DEFAULTS: AppSettings = {
  model: "openrouter/google/gemini-3-flash-preview",
  customModel: "",
  useCustomModel: false,
  apiKey: "",
  preamble: "",
  maxRetries: null,
  dpi: null,
  temperature: null,
  maxTokens: null,
};

export function loadSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULTS };
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULTS };
  }
}

export function saveSettings(settings: AppSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
}

export function getEffectiveModel(settings: AppSettings): string {
  return settings.useCustomModel ? settings.customModel : settings.model;
}
