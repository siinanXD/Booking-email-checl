import { useQuery } from "@tanstack/react-query";
import { fetchReviewQueue } from "@/lib/api/review";
import { Card } from "@/shared/ui/Card";
import { IntentBadge } from "@/shared/components/IntentBadge";

export function CompletedPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["review-queue", "completed"],
    queryFn: () => fetchReviewQueue("completed", 100),
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-slate-800">Abgeschlossen</h2>
      <Card className="p-0">
        {isLoading ? (
          <p className="p-4 text-slate-500">Lade…</p>
        ) : (data?.items.length ?? 0) === 0 ? (
          <p className="p-4 text-slate-500">Noch keine abgeschlossenen Reviews.</p>
        ) : (
          <ul>
            {data!.items.map((item) => (
              <li
                key={item.correlation_id}
                className="border-b border-slate-100 px-4 py-3"
              >
                <p className="font-medium text-sm">{item.subject}</p>
                <p className="text-xs text-slate-500">{item.from_address}</p>
                <div className="mt-1">
                  <IntentBadge intent={item.intent} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
