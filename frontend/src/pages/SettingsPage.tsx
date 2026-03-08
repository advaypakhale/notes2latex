import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ExternalLink, RotateCcw, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { loadSettings, saveSettings, type AppSettings } from "@/lib/settings";
import { fetchDefaultPreamble } from "@/lib/api";

const MODELS = [
  {
    group: "Google",
    items: [
      {
        value: "openrouter/google/gemini-3-flash-preview",
        label: "Gemini 3 Flash",
      },
      {
        value: "openrouter/google/gemini-2.5-pro-preview",
        label: "Gemini 2.5 Pro",
      },
    ],
  },
  {
    group: "Anthropic",
    items: [
      { value: "anthropic/claude-sonnet-4-6", label: "Claude Sonnet 4.6" },
      {
        value: "anthropic/claude-haiku-4-5-20251001",
        label: "Claude Haiku 4.5",
      },
    ],
  },
  {
    group: "OpenAI",
    items: [
      { value: "openai/gpt-4o", label: "GPT-4o" },
      { value: "openai/gpt-4.1-mini", label: "GPT-4.1 Mini" },
    ],
  },
];

export function SettingsPage() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState<AppSettings>(loadSettings);
  const [saved, setSaved] = useState(false);
  const [defaultPreamble, setDefaultPreamble] = useState("");

  useEffect(() => {
    fetchDefaultPreamble()
      .then((preamble) => {
        setDefaultPreamble(preamble);
        // If no custom preamble is set yet, populate with the default
        setSettings((prev) => {
          if (!prev.preamble) {
            return { ...prev, preamble };
          }
          return prev;
        });
      })
      .catch(() => {});
  }, []);

  const update = (patch: Partial<AppSettings>) => {
    setSettings((prev) => ({ ...prev, ...patch }));
    setSaved(false);
  };

  const handleSave = () => {
    saveSettings(settings);
    setSaved(true);
  };

  return (
    <div className="container mx-auto max-w-2xl py-8 px-4">
      <Button
        variant="ghost"
        size="sm"
        className="mb-6 -ml-2"
        onClick={() => navigate("/")}
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>Settings</CardTitle>
          <CardDescription>
            Configure your model and API key. These are saved locally in your
            browser and used for all future conversions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Model selector */}
          <div className="space-y-2">
            <Label>Model</Label>
            {!settings.useCustomModel ? (
              <Select
                value={settings.model}
                onValueChange={(v) => update({ model: v })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {MODELS.map((group) => (
                    <SelectGroup key={group.group}>
                      <SelectLabel>{group.group}</SelectLabel>
                      {group.items.map((item) => (
                        <SelectItem key={item.value} value={item.value}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectGroup>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                placeholder="e.g. openrouter/meta-llama/llama-4-scout"
                value={settings.customModel}
                onChange={(e) => update({ customModel: e.target.value })}
              />
            )}
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground underline"
              onClick={() =>
                update({ useCustomModel: !settings.useCustomModel })
              }
            >
              {settings.useCustomModel
                ? "Use preset models"
                : "Enter custom model string"}
            </button>
          </div>

          <Separator />

          {/* API Key */}
          <div className="space-y-2">
            <Label>API Key</Label>
            <Input
              type="password"
              placeholder="sk-..."
              value={settings.apiKey}
              onChange={(e) => update({ apiKey: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">
              Your key is stored only in this browser and sent directly to the
              provider. Leave blank to use server defaults.
            </p>
          </div>

          <Separator />

          {/* Preamble editor */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>LaTeX Preamble</Label>
              {defaultPreamble && settings.preamble !== defaultPreamble && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    update({ preamble: defaultPreamble });
                  }}
                >
                  <RotateCcw className="mr-1 h-3 w-3" />
                  Reset to Default
                </Button>
              )}
            </div>
            <Textarea
              className="font-mono text-xs leading-relaxed min-h-[320px] resize-y"
              value={settings.preamble}
              onChange={(e) => update({ preamble: e.target.value })}
              spellCheck={false}
            />
            <p className="text-xs text-muted-foreground">
              Customize the LaTeX preamble used for all conversions. Add your
              own <code>\newcommand</code> definitions, packages, and theorem
              styles.
            </p>
          </div>

          <Separator />

          {/* Advanced settings */}
          <details className="group">
            <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium list-none">
              <ChevronDown className="h-4 w-4 transition-transform group-open:rotate-180" />
              Advanced
            </summary>
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label htmlFor="max-retries" className="text-sm">
                    Max Retries
                  </Label>
                  <Input
                    id="max-retries"
                    type="number"
                    min={0}
                    placeholder="3"
                    value={settings.maxRetries ?? ""}
                    onChange={(e) =>
                      update({
                        maxRetries: e.target.value
                          ? Number(e.target.value)
                          : null,
                      })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Fix attempts per page
                  </p>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="dpi" className="text-sm">
                    DPI
                  </Label>
                  <Input
                    id="dpi"
                    type="number"
                    min={72}
                    placeholder="300"
                    value={settings.dpi ?? ""}
                    onChange={(e) =>
                      update({
                        dpi: e.target.value ? Number(e.target.value) : null,
                      })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    PDF rasterization resolution
                  </p>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="temperature" className="text-sm">
                    Temperature
                  </Label>
                  <Input
                    id="temperature"
                    type="number"
                    min={0}
                    max={2}
                    step={0.1}
                    placeholder="0.1"
                    value={settings.temperature ?? ""}
                    onChange={(e) =>
                      update({
                        temperature: e.target.value
                          ? Number(e.target.value)
                          : null,
                      })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    LLM sampling temperature
                  </p>
                </div>
                <div className="space-y-1">
                  <Label htmlFor="max-tokens" className="text-sm">
                    Max Tokens
                  </Label>
                  <Input
                    id="max-tokens"
                    type="number"
                    min={1}
                    placeholder="16384"
                    value={settings.maxTokens ?? ""}
                    onChange={(e) =>
                      update({
                        maxTokens: e.target.value
                          ? Number(e.target.value)
                          : null,
                      })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    Max tokens per LLM call
                  </p>
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Leave blank to use server defaults. These can also be set via
                environment variables with the <code>NOTES2LATEX_</code> prefix.
              </p>
            </div>
          </details>

          <Separator />

          {/* Docs link */}
          <div className="text-sm text-muted-foreground">
            <a
              href="https://docs.litellm.ai/docs/providers"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 underline hover:text-foreground"
            >
              Supported model providers
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {/* Save */}
          <div className="flex items-center gap-3">
            <Button onClick={handleSave}>Save Settings</Button>
            {saved && (
              <span className="text-sm text-muted-foreground">Saved</span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
