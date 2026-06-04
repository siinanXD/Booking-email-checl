import { useQuery } from "@tanstack/react-query";
import { fetchAdminLlmPromptHistory } from "@/lib/api/admin";
import type { AdminLlmPromptType } from "@/lib/types/api";
import { Button } from "@/shared/ui/Button";

function previewText(text: string | null, maxLen = 120): string {
  if (!text) return "(Standard-Prompt aus Datei)";
  const oneLine = text.replace(/\s+/g, " ").trim();
  if (oneLine.length <= maxLen) return oneLine;
  return `${oneLine.slice(0, maxLen)}…`;
}

interface PromptHistoryPanelProps {
  promptType: AdminLlmPromptType;
  currentText: string;
  onRestore: (text: string) => void;
}

export function PromptHistoryPanel({
  promptType,
  currentText,
  onRestore,
}: PromptHistoryPanelProps) {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-llm-prompt-history", promptType],
    queryFn: () => fetchAdminLlmPromptHistory(promptType),
  });

  const entries = data?.entries ?? [];

  if (isLoading) {
    return <p className="text-xs text-slate-500">Lade Prompt-Historie…</p>;
  }

  if (entries.length === 0) {
    return (
      <p className="text-xs text-slate-500">
        Noch keine gespeicherten Versionen — nach dem ersten Speichern erscheint hier die
        Historie.
      </p>
    );
  }

  return (
    <div className="space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3">
      <h4 className="text-sm font-medium text-slate-800">
        Prompt-Historie ({entries.length})
      </h4>
      <ul className="max-h-64 space-y-2 overflow-y-auto">
        {entries.map((entry) => {
          const restoredText = entry.prompt_text ?? "";
          const isCurrent = restoredText === currentText.trim();
          return (
            <li
              key={entry.id}
              className="rounded border border-slate-200 bg-white p-2 text-xs"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <time className="text-slate-500">
                  {new Date(entry.created_at).toLocaleString("de-DE")}
                </time>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="secondary"
                    className="px-2 py-1 text-xs"
                    onClick={() => onRestore(restoredText)}
                  >
                    Wiederherstellen
                  </Button>
                </div>
              </div>
              <p className="mt-1 font-mono text-slate-700">{previewText(entry.prompt_text)}</p>
              {isCurrent && (
                <p className="mt-1 text-emerald-700">Entspricht dem aktuellen Textfeld</p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
