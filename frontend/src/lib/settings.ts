const STORAGE_KEY = "n2l_settings";

export interface AppSettings {
  model: string;
  customModel: string;
  useCustomModel: boolean;
  apiKey: string;
  preamble: string;
  transcribePrompt: string;
}

const DEFAULTS: AppSettings = {
  model: "openrouter/google/gemini-3-flash-preview",
  customModel: "",
  useCustomModel: false,
  apiKey: "",
  preamble: "",
  transcribePrompt: "",
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
