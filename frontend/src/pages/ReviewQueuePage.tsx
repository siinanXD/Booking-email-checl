import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { fetchEmailDetail, fetchEmails } from "@/api/emails";
import { approveReview, rejectReview } from "@/api/review";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import type { EmailListItem } from "@/types/api";

export function ReviewQueuePage() {
  const [selected, setSelected] = useState<EmailListItem | null>(null);
  const [draftEdit, setDraftEdit] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const queryClient = useQueryClient();

  const { data: list, isLoading } = useQuery({
    queryKey: ["review-queue"],
    queryFn: () => fetchEmails({ status: "pending_review", limit: 50 }),
  });

  const { data: detail } = useQuery({
    queryKey: ["email-detail", selected?.correlation_id],
    queryFn: () => fetchEmailDetail(selected!.correlation_id),
    enabled: Boolean(selected?.correlation_id),
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
  };

  const approveMut = useMutation({
    mutationFn: () =>
      approveReview(selected!.correlation_id, draftEdit || undefined),
    onSuccess: () => {
      setSelected(null);
      invalidate();
    },
  });

  const rejectMut = useMutation({
    mutationFn: () => rejectReview(selected!.correlation_id, rejectReason),
    onSuccess: () => {
      setSelected(null);
      setRejectReason("");
      invalidate();
    },
  });

  useEffect(() => {
    if (detail?.draft_body) {
      setDraftEdit(detail.draft_body);
    }
  }, [detail?.correlation_id, detail?.draft_body]);

  function selectItem(item: EmailListItem) {
    setSelected(item);
    setDraftEdit("");
    setRejectReason("");
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-slate-800">Review-Warteschlange</h2>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="max-h-[70vh] overflow-y-auto p-0">
          {isLoading ? (
            <p className="p-4 text-slate-500">Lade…</p>
          ) : (list?.items.length ?? 0) === 0 ? (
            <p className="p-4 text-slate-500">Keine ausstehenden Reviews</p>
          ) : (
            <ul>
              {list!.items.map((item) => (
                <li key={item.correlation_id}>
                  <button
                    type="button"
                    className={`w-full border-b border-slate-100 px-4 py-3 text-left hover:bg-slate-50 ${
                      selected?.correlation_id === item.correlation_id
                        ? "bg-indigo-50"
                        : ""
                    }`}
                    onClick={() => selectItem(item)}
                  >
                    <p className="font-medium text-sm">{item.subject}</p>
                    <p className="text-xs text-slate-500">{item.from_address}</p>
                    <div className="mt-1 flex gap-2">
                      <Badge label={item.intent ?? "—"} tone="pending" />
                      {item.grounding_flag && (
                        <Badge label="Grounding" tone="rejected" />
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          {!selected ? (
            <p className="text-slate-500">E-Mail aus der Liste wählen</p>
          ) : !detail ? (
            <p className="text-slate-500">Lade Detail…</p>
          ) : (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">{detail.subject}</h3>
                <p className="text-sm text-slate-500">{detail.from_address}</p>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium uppercase text-slate-500">
                  Original
                </p>
                <pre className="max-h-32 overflow-auto rounded bg-slate-50 p-3 text-xs whitespace-pre-wrap">
                  {detail.body_text || "—"}
                </pre>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium uppercase text-slate-500">
                  Entwurf (bearbeitbar)
                </p>
                <textarea
                  className="h-40 w-full rounded-lg border border-slate-300 p-3 text-sm"
                  value={draftEdit || detail.draft_body}
                  onChange={(e) => setDraftEdit(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={() => approveMut.mutate()}
                  disabled={approveMut.isPending}
                >
                  Freigeben
                </Button>
              </div>
              <div className="border-t pt-4">
                <p className="mb-2 text-sm text-slate-600">Ablehnen</p>
                <Input
                  placeholder="Grund (optional)"
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                />
                <Button
                  variant="danger"
                  className="mt-2"
                  onClick={() => rejectMut.mutate()}
                  disabled={rejectMut.isPending}
                >
                  Ablehnen
                </Button>
              </div>
              {(approveMut.isError || rejectMut.isError) && (
                <p className="text-sm text-red-600">
                  Aktion fehlgeschlagen. Bitte erneut versuchen.
                </p>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
