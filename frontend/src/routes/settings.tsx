import { useQuery } from "@tanstack/react-query";
import { ExternalLinkIcon, RotateCcwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldSeparator,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { BackLink } from "@/components/back-link";
import { defaultPreambleQuery } from "@/api/queries";
import { useSettings } from "@/stores/settings";

const modelGroups = [
  {
    provider: "Google",
    models: [
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
    provider: "Anthropic",
    models: [
      { value: "anthropic/claude-sonnet-4-6", label: "Claude Sonnet 4.6" },
      {
        value: "anthropic/claude-haiku-4-5-20251001",
        label: "Claude Haiku 4.5",
      },
    ],
  },
  {
    provider: "OpenAI",
    models: [
      { value: "openai/gpt-4o", label: "GPT-4o" },
      { value: "openai/gpt-4.1-mini", label: "GPT-4.1 Mini" },
    ],
  },
];

const modelItems = modelGroups.flatMap((group) => group.models);

export function Settings() {
  const settings = useSettings();
  const defaultPreamble = useQuery(defaultPreambleQuery);

  return (
    <div className="container mx-auto max-w-2xl px-4 py-8">
      <BackLink />

      <Card>
        <CardHeader>
          <CardTitle>Settings</CardTitle>
          <CardDescription>
            Configure your model and API key. These are saved in this browser as
            you type and used for all future conversions.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="model">Model</FieldLabel>
              {settings.useCustomModel ? (
                <Input
                  id="model"
                  placeholder="e.g. openrouter/meta-llama/llama-4-scout"
                  value={settings.customModel}
                  onChange={(e) =>
                    settings.update({ customModel: e.target.value })
                  }
                />
              ) : (
                <Select
                  items={modelItems}
                  value={settings.model}
                  onValueChange={(model) =>
                    settings.update({ model: model ?? "" })
                  }
                >
                  <SelectTrigger id="model" className="w-full">
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent>
                    {modelGroups.map((group) => (
                      <SelectGroup key={group.provider}>
                        <SelectLabel>{group.provider}</SelectLabel>
                        {group.models.map((model) => (
                          <SelectItem key={model.value} value={model.value}>
                            {model.label}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Button
                variant="link"
                size="xs"
                className="w-fit! px-0 text-muted-foreground"
                onClick={() =>
                  settings.update({ useCustomModel: !settings.useCustomModel })
                }
              >
                {settings.useCustomModel
                  ? "Use preset models"
                  : "Enter custom model string"}
              </Button>
            </Field>

            <FieldSeparator />

            <Field>
              <FieldLabel htmlFor="api-key">API Key</FieldLabel>
              <Input
                id="api-key"
                type="password"
                placeholder="sk-..."
                value={settings.apiKey}
                onChange={(e) => settings.update({ apiKey: e.target.value })}
              />
              <FieldDescription>
                Your key is stored only in this browser and sent directly to the
                provider. Leave blank to use server defaults.
              </FieldDescription>
            </Field>

            <FieldSeparator />

            <Field>
              <FieldLabel htmlFor="preamble">LaTeX Preamble</FieldLabel>
              <Textarea
                id="preamble"
                className="max-h-[60vh] min-h-80 resize-y font-mono text-xs leading-relaxed"
                placeholder={defaultPreamble.data}
                value={settings.preamble}
                onChange={(e) => settings.update({ preamble: e.target.value })}
                spellCheck={false}
              />
              <FieldDescription>
                Customize the LaTeX preamble used for all conversions. Add your
                own <code>\newcommand</code> definitions, packages, and theorem
                styles. Leave it empty to use the server's preamble, shown here
                greyed out.
              </FieldDescription>
              <Button
                variant="link"
                size="xs"
                className="w-fit! px-0 text-muted-foreground"
                disabled={!defaultPreamble.data}
                onClick={() =>
                  settings.update({
                    preamble: settings.preamble
                      ? ""
                      : (defaultPreamble.data ?? ""),
                  })
                }
              >
                <RotateCcwIcon />
                {settings.preamble
                  ? "Reset to default"
                  : "Start from the default"}
              </Button>
            </Field>

            <FieldSeparator />

            <FieldDescription>
              <a
                href="https://docs.litellm.ai/docs/providers"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1"
              >
                Supported model providers
                <ExternalLinkIcon className="size-3" />
              </a>
            </FieldDescription>
          </FieldGroup>
        </CardContent>
      </Card>
    </div>
  );
}
