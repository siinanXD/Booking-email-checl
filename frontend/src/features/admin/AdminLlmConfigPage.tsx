import { Card } from "@/shared/ui/Card";

export function AdminLlmConfigPage() {
  return (
    <Card className="space-y-2">
      <h2 className="text-lg font-medium text-slate-900">LLM-Konfiguration</h2>
      <p className="text-sm text-slate-600">
        Prompt-Overrides, Temperatur und Similarity Top-K folgen in Phase 4.
      </p>
    </Card>
  );
}
