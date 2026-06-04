import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useAuthStore } from "@/features/auth/authStore";
import { createWorkflowApi } from "@/lib/api/workflows";
import type {
  TenantWorkflowCreateRequest,
  TenantWorkflowSuggestResponse,
  WorkflowImportance,
  WorkflowLlmProvider,
  WorkflowMediaAttachment,
} from "@/lib/types/api";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";

type EditorMode = "list" | "create" | "edit";

const EMPTY_FORM: TenantWorkflowCreateRequest = {
  label: "",
  slug: "",
  description: "",
  search_hints: "",
  importance: "medium",
  required_fields: [],
  optional_fields: [],
  extraction_schema: {},
  classify_prompt: "",
  extract_prompt: "",
  draft_prompt: "",
  test_emails: [],
  match_rules: { subject_keywords: [], from_domains: [], body_keywords: [] },
  llm_provider: "openai",
  supports_multimodal: false,
  multimodal_prompt: "",
  enabled: false,
  sandbox_only: true,
  priority: 0,
};

function applySuggestion(
  suggestion: TenantWorkflowSuggestResponse
): TenantWorkflowCreateRequest {
  return {
    ...EMPTY_FORM,
    label: suggestion.label,
    slug: suggestion.slug,
    description: suggestion.description,
    search_hints: suggestion.search_hints,
    importance: suggestion.importance,
    required_fields: suggestion.required_fields,
    optional_fields: suggestion.optional_fields,
    extraction_schema: suggestion.extraction_schema,
    classify_prompt: suggestion.classify_prompt,
    extract_prompt: suggestion.extract_prompt,
    test_emails: suggestion.test_emails,
    match_rules: suggestion.match_rules,
    llm_provider: suggestion.llm_provider,
    supports_multimodal: suggestion.supports_multimodal,
    multimodal_prompt: suggestion.multimodal_prompt ?? "",
    enabled: false,
    sandbox_only: true,
  };
}

function fieldsToText(fields: string[]): string {
  return fields.join(", ");
}

function textToFields(text: string): string[] {
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

async function filesToAttachments(files: FileList | null): Promise<WorkflowMediaAttachment[]> {
  if (!files?.length) return [];
  const allowed = new Set([
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
  ]);
  const out: WorkflowMediaAttachment[] = [];
  for (const file of Array.from(files).slice(0, 5)) {
    if (!allowed.has(file.type)) continue;
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.length; i += 1) {
      binary += String.fromCharCode(bytes[i] ?? 0);
    }
    out.push({
      filename: file.name,
      mime_type: file.type,
      data_base64: btoa(binary),
    });
  }
  return out;
}

export interface WorkflowsPageProps {
  /** Plattform-Admin: Workflows für diesen Mandanten bearbeiten. */
  adminAccountId?: string;
  subtitle?: string;
}

export function WorkflowsPage(props: WorkflowsPageProps = {}) {
  const { adminAccountId, subtitle } = props;
  const queryClient = useQueryClient();
  const isPlatformAdmin = useAuthStore((s) => s.isPlatformAdmin());
  const api = useMemo(() => createWorkflowApi(adminAccountId), [adminAccountId]);
  const queryKey = useMemo(
    () => (adminAccountId ? ["workflows", "admin", adminAccountId] : ["workflows"]),
    [adminAccountId]
  );
  const [mode, setMode] = useState<EditorMode>("list");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<TenantWorkflowCreateRequest>(EMPTY_FORM);
  const [assistDescription, setAssistDescription] = useState("");
  const [assistFiles, setAssistFiles] = useState<FileList | null>(null);
  const [previewSubject, setPreviewSubject] = useState("Test-Betreff");
  const [previewBody, setPreviewBody] = useState("Test-Inhalt");
  const [previewResult, setPreviewResult] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [previewNotice, setPreviewNotice] = useState<string | null>(null);
  const [previewFiles, setPreviewFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [testsPassed, setTestsPassed] = useState(false);

  const { data: list, isLoading } = useQuery({
    queryKey,
    queryFn: () => api.fetchWorkflows(),
    enabled: Boolean(adminAccountId) || isPlatformAdmin,
  });

  const { data: geminiStatus } = useQuery({
    queryKey: [...queryKey, "gemini-status"],
    queryFn: () => api.fetchGeminiStatus(),
    enabled: Boolean(adminAccountId) || isPlatformAdmin,
  });

  const suggestMut = useMutation({
    mutationFn: async () => {
      const attachments = await filesToAttachments(assistFiles);
      const description =
        assistDescription.trim() ||
        (attachments.length > 0 ? "Workflow aus Beispiel-Screenshot" : "");
      return api.suggestWorkflow({
        description,
        label_hint: form.label || null,
        attachments,
      });
    },
    onSuccess: (res) => {
      setForm(applySuggestion(res));
      if (res.test_emails[0]) {
        setPreviewSubject(res.test_emails[0].subject);
        setPreviewBody(res.test_emails[0].body);
      }
      setMessage(
        res.supports_multimodal
          ? "KI-Vorschlag aus Beispiel übernommen (Felder, Regeln, Test-Mail) — bitte prüfen und speichern."
          : "KI-Vorschlag übernommen — bitte prüfen und speichern."
      );
    },
    onError: (err: unknown) => {
      const msg =
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response &&
        err.response.data &&
        typeof err.response.data === "object" &&
        "error" in err.response.data &&
        typeof err.response.data.error === "string"
          ? err.response.data.error
          : "KI-Vorschlag fehlgeschlagen.";
      setMessage(msg);
    },
  });

  const saveMut = useMutation({
    mutationFn: async () => {
      if (mode === "edit" && editingId) {
        return api.updateWorkflow(editingId, form);
      }
      return api.createWorkflow(form);
    },
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey });
      setEditingId(saved.id);
      setMode("edit");
      setTestsPassed(
        Boolean(
          saved.last_test_passed_at &&
            saved.last_test_passed_total > 0 &&
            saved.last_test_passed_count === saved.last_test_passed_total
        )
      );
      setMessage("Workflow gespeichert.");
    },
    onError: () => setMessage("Speichern fehlgeschlagen."),
  });

  const deleteMut = useMutation({
    mutationFn: () => api.deleteWorkflow(editingId!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
      setMode("list");
      setEditingId(null);
      setForm(EMPTY_FORM);
      setMessage("Workflow gelöscht.");
    },
  });

  const previewMut = useMutation({
    mutationFn: async () => {
      const attachments = await filesToAttachments(previewFiles);
      return api.previewWorkflow(editingId!, {
        subject: previewSubject,
        body: previewBody,
        attachments,
      });
    },
    onSuccess: (res) => {
      setPreviewResult(res.success ? res.result : null);
      setPreviewError(res.success ? null : res.error ?? "Unbekannter Fehler");
      setPreviewNotice(res.notice ?? null);
    },
  });

  const testsMut = useMutation({
    mutationFn: () => api.runWorkflowTests(editingId!),
    onSuccess: (res) => {
      const ok = res.total > 0 && res.passed === res.total;
      setTestsPassed(ok);
      setMessage(
        ok
          ? `Test-Suite bestanden (${res.passed}/${res.total}). Live-Aktivierung möglich.`
          : `Test-Suite: ${res.passed}/${res.total} — Live-Aktivierung gesperrt.`
      );
      void queryClient.invalidateQueries({ queryKey });
    },
  });

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
    setAssistDescription("");
    setAssistFiles(null);
    setPreviewResult(null);
    setPreviewError(null);
    setMessage(null);
    setMode("create");
  };

  const openEdit = async (id: string) => {
    const wf = await api.fetchWorkflow(id);
    setForm({
      label: wf.label,
      slug: wf.slug,
      description: wf.description,
      search_hints: wf.search_hints,
      importance: wf.importance,
      required_fields: wf.required_fields,
      optional_fields: wf.optional_fields,
      extraction_schema: wf.extraction_schema,
      classify_prompt: wf.classify_prompt,
      extract_prompt: wf.extract_prompt,
      draft_prompt: wf.draft_prompt,
      few_shot_examples: wf.few_shot_examples,
      test_emails: wf.test_emails,
      match_rules: wf.match_rules,
      llm_provider: wf.llm_provider,
      supports_multimodal: wf.supports_multimodal,
      multimodal_prompt: wf.multimodal_prompt,
      enabled: wf.enabled,
      sandbox_only: wf.sandbox_only,
      priority: wf.priority,
    });
    setEditingId(id);
    setMode("edit");
    setTestsPassed(
      Boolean(
        wf.last_test_passed_at &&
          wf.last_test_passed_total > 0 &&
          wf.last_test_passed_count === wf.last_test_passed_total
      )
    );
    setMessage(null);
    if (wf.test_emails[0]) {
      setPreviewSubject(wf.test_emails[0].subject);
      setPreviewBody(wf.test_emails[0].body);
    }
  };

  if (!adminAccountId && !isPlatformAdmin) {
    return (
      <Card>
        <p className="text-sm text-slate-600">
          Workflow-Verwaltung ist nur für Plattform-Administratoren verfügbar
          (Menü Admin → Workflows, Mandant wählen).
        </p>
      </Card>
    );
  }

  const pageSubtitle =
    subtitle ??
    (adminAccountId
      ? "Workflows dieses Mandanten — Live-Routing wenn aktiviert und Tests grün."
      : "Eigene Regeln und Prompts — Live-Routing wenn aktiviert und Tests grün.");

  if (mode === "list") {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Workflows</h1>
            <p className="mt-1 text-sm text-slate-600">{pageSubtitle}</p>
          </div>
          <Button onClick={openCreate}>Neuer Workflow</Button>
        </div>

        {isLoading && <p className="text-sm text-slate-500">Lade…</p>}

        <div className="grid gap-4 md:grid-cols-2">
          {(list?.items ?? []).map((wf) => (
            <Card key={wf.id} className="space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h2 className="font-medium text-slate-900">{wf.label}</h2>
                  <p className="text-xs text-slate-500">{wf.slug}</p>
                </div>
                <div className="flex flex-wrap gap-1">
                  {wf.sandbox_only && <Badge label="Sandbox" tone="pending" />}
                  {wf.tests_passed && <Badge label="Tests OK" tone="approved" />}
                  {wf.enabled && <Badge label="Live" tone="approved" />}
                  {wf.supports_multimodal && (
                    <Badge label="Multimodal" tone="default" />
                  )}
                </div>
              </div>
              <p className="text-sm text-slate-600 line-clamp-2">{wf.description}</p>
              <p className="text-xs text-slate-500">
                {wf.test_email_count} Test-Mail(s) · Wichtigkeit: {wf.importance}
              </p>
              <Button variant="secondary" onClick={() => void openEdit(wf.id)}>
                Bearbeiten
              </Button>
            </Card>
          ))}
        </div>

        {!isLoading && (list?.items.length ?? 0) === 0 && (
          <Card className="text-sm text-slate-600">
            Noch keine Workflows. Lege einen an — der KI-Assistent schlägt Felder
            und Prompts vor.
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="secondary" onClick={() => setMode("list")}>
          ← Zurück
        </Button>
        <h1 className="text-xl font-semibold text-slate-900">
          {mode === "create" ? "Workflow anlegen" : form.label || "Workflow"}
        </h1>
      </div>

      {message && <p className="text-sm text-slate-600">{message}</p>}

      <Card className="space-y-3">
        <h2 className="font-medium text-slate-900">KI-Assistent</h2>
        <p className="text-xs text-slate-500">
          Lade einen Screenshot oder ein PDF einer Beispiel-Mail hoch — Gemini
          schlägt Felder, Routing-Keywords und eine Test-Mail vor. Optional
          ergänzt du eine kurze Beschreibung.
        </p>
        <label className="block text-sm text-slate-600">
          Beispiel-Mail (Screenshot/PDF, max. 5)
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            multiple
            className="mt-1 block w-full text-sm"
            onChange={(e) => setAssistFiles(e.target.files)}
          />
        </label>
        <textarea
          className="min-h-[100px] w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={assistDescription}
          onChange={(e) => setAssistDescription(e.target.value)}
          placeholder="Optional: z.B. Tracking-Mails von DHL — Sendungsnummer ist Pflicht."
        />
        {assistFiles?.length && geminiStatus && !geminiStatus.available && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
            GEMINI_API_KEY fehlt — Screenshot-Vorschläge sind nur mit Gemini möglich.
          </p>
        )}
        <Button
          variant="secondary"
          disabled={
            (assistDescription.trim().length < 10 && !assistFiles?.length) ||
            suggestMut.isPending ||
            Boolean(assistFiles?.length && geminiStatus && !geminiStatus.available)
          }
          onClick={() => suggestMut.mutate()}
        >
          Vorschlag generieren
        </Button>
      </Card>

      <Card className="space-y-4">
        <h2 className="font-medium text-slate-900">Grunddaten</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm text-slate-600">
            Name
            <Input
              className="mt-1"
              value={form.label}
              onChange={(e) => setForm({ ...form, label: e.target.value })}
            />
          </label>
          <label className="block text-sm text-slate-600">
            Slug
            <Input
              className="mt-1 font-mono text-xs"
              value={form.slug ?? ""}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
            />
          </label>
        </div>
        <label className="block text-sm text-slate-600">
          Beschreibung
          <textarea
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </label>
        <label className="block text-sm text-slate-600">
          Suchhinweise
          <textarea
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={form.search_hints}
            onChange={(e) => setForm({ ...form, search_hints: e.target.value })}
          />
        </label>
        <label className="block text-sm text-slate-600">
          Wichtigkeit
          <select
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={form.importance}
            onChange={(e) =>
              setForm({
                ...form,
                importance: e.target.value as WorkflowImportance,
              })
            }
          >
            <option value="high">Hoch</option>
            <option value="medium">Mittel</option>
            <option value="low">Niedrig</option>
          </select>
        </label>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm text-slate-600">
            Pflichtfelder (kommagetrennt)
            <Input
              className="mt-1 font-mono text-xs"
              value={fieldsToText(form.required_fields ?? [])}
              onChange={(e) =>
                setForm({ ...form, required_fields: textToFields(e.target.value) })
              }
            />
          </label>
          <label className="block text-sm text-slate-600">
            Optionale Felder
            <Input
              className="mt-1 font-mono text-xs"
              value={fieldsToText(form.optional_fields ?? [])}
              onChange={(e) =>
                setForm({ ...form, optional_fields: textToFields(e.target.value) })
              }
            />
          </label>
        </div>
        <label className="block text-sm text-slate-600">
          LLM-Provider
          <select
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={form.llm_provider ?? "openai"}
            onChange={(e) =>
              setForm({
                ...form,
                llm_provider: e.target.value as WorkflowLlmProvider,
              })
            }
          >
            <option value="openai">OpenAI (Text)</option>
            <option value="gemini">Gemini (Multimodal Sandbox)</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={form.supports_multimodal}
            onChange={(e) => {
              const checked = e.target.checked;
              setForm({
                ...form,
                supports_multimodal: checked,
                llm_provider: checked ? "gemini" : form.llm_provider,
              });
            }}
          />
          Multimodal (Bilder/PDF in Preview/Tests)
        </label>
        {form.llm_provider === "gemini" && geminiStatus && !geminiStatus.available && (
          <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
            GEMINI_API_KEY fehlt in der Server-.env (Google AI Studio). OpenAI bleibt
            für andere Schritte aktiv; Gemini-Preview schlägt fehl bis der Key gesetzt ist.
          </p>
        )}
        {form.supports_multimodal && (
          <label className="block text-sm text-slate-600">
            Multimodal-Prompt
            <textarea
              className="mt-1 min-h-[80px] w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={form.multimodal_prompt ?? ""}
              onChange={(e) =>
                setForm({ ...form, multimodal_prompt: e.target.value })
              }
              placeholder="z.B. Lies Rechnungsbeträge und Bestellnummern aus Screenshots/PDFs."
            />
          </label>
        )}
        {form.llm_provider === "gemini" && (
          <p className="text-xs text-slate-500">
            Live-Workflows nutzen Gemini nur mit Mail-Text; Anhänge aus echten Mails
            kommen in einer späteren Phase.
          </p>
        )}
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={form.sandbox_only ?? true}
            onChange={(e) => setForm({ ...form, sandbox_only: e.target.checked })}
          />
          Nur Sandbox (empfohlen bis Tests grün)
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={form.enabled ?? false}
            disabled={!testsPassed}
            onChange={(e) =>
              setForm({
                ...form,
                enabled: e.target.checked,
                sandbox_only: e.target.checked ? form.sandbox_only : false,
              })
            }
          />
          Live aktiv (Routing auf eingehende Mails)
        </label>
        {!testsPassed && (
          <p className="text-xs text-amber-700">
            Live-Aktivierung erst nach bestandener Test-Suite möglich.
          </p>
        )}
      </Card>

      <Card className="space-y-3">
        <h2 className="font-medium text-slate-900">Prompts</h2>
        <label className="block text-sm text-slate-600">
          Klassifikation
          <textarea
            className="mt-1 min-h-[120px] w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs"
            value={form.classify_prompt}
            onChange={(e) => setForm({ ...form, classify_prompt: e.target.value })}
          />
        </label>
        <label className="block text-sm text-slate-600">
          Extraktion (Platzhalter: {"{subject}"}, {"{body}"})
          <textarea
            className="mt-1 min-h-[160px] w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs"
            value={form.extract_prompt}
            onChange={(e) => setForm({ ...form, extract_prompt: e.target.value })}
          />
        </label>
      </Card>

      <Card className="space-y-3">
        <h2 className="font-medium text-slate-900">Routing-Hinweise (für Phase B)</h2>
        <label className="block text-sm text-slate-600">
          Betreff-Keywords (kommagetrennt)
          <Input
            className="mt-1"
            value={fieldsToText(form.match_rules?.subject_keywords ?? [])}
            onChange={(e) =>
              setForm({
                ...form,
                match_rules: {
                  ...form.match_rules!,
                  subject_keywords: textToFields(e.target.value),
                },
              })
            }
          />
        </label>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Button disabled={saveMut.isPending} onClick={() => saveMut.mutate()}>
          Speichern
        </Button>
        {editingId && (
          <>
            <Button
              variant="secondary"
              disabled={previewMut.isPending}
              onClick={() => previewMut.mutate()}
            >
              Preview
            </Button>
            <Button
              variant="secondary"
              disabled={testsMut.isPending}
              onClick={() => testsMut.mutate()}
            >
              Test-Suite
            </Button>
            <Button
              variant="danger"
              disabled={deleteMut.isPending}
              onClick={() => {
                if (window.confirm("Workflow wirklich löschen?")) {
                  deleteMut.mutate();
                }
              }}
            >
              Löschen
            </Button>
          </>
        )}
      </div>

      {editingId && (
        <Card className="space-y-3">
          <h2 className="font-medium text-slate-900">Preview</h2>
          <Input
            value={previewSubject}
            onChange={(e) => setPreviewSubject(e.target.value)}
            placeholder="Betreff"
          />
          <textarea
            className="min-h-[80px] w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={previewBody}
            onChange={(e) => setPreviewBody(e.target.value)}
          />
          {form.supports_multimodal && form.llm_provider === "gemini" && (
            <label className="block text-sm text-slate-600">
              Anhänge (JPEG, PNG, WebP, PDF — max. 5)
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,application/pdf"
                multiple
                className="mt-1 block w-full text-sm"
                onChange={(e) => setPreviewFiles(e.target.files)}
              />
            </label>
          )}
          {previewNotice && (
            <p className="text-xs text-amber-800">{previewNotice}</p>
          )}
          {previewError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              {previewError}
            </div>
          )}
          {previewResult && (
            <pre className="max-h-48 overflow-auto rounded bg-emerald-50 p-3 text-xs">
              {previewResult}
            </pre>
          )}
        </Card>
      )}
    </div>
  );
}
