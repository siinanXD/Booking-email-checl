import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchBookings, fetchEmails, type EmailListParams } from "@/lib/api/emails";
import { EmailTable } from "@/shared/components/EmailTable";
import { Input } from "@/shared/ui/Input";

type ListMode = "bookings" | "emails";

export function EmailListPage({
  title,
  subtitle,
  params,
  mode = "emails",
}: {
  title: string;
  subtitle?: string;
  params?: EmailListParams;
  mode?: ListMode;
}) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const queryParams: EmailListParams = {
    ...params,
    search: search || undefined,
    page,
    limit: 20,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["email-list", mode, queryParams],
    queryFn: () =>
      mode === "bookings" ? fetchBookings(queryParams) : fetchEmails(queryParams),
  });

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">{title}</h2>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </div>
      <Input
        placeholder="Suche (Betreff, Buchungsnr.)…"
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setPage(1);
        }}
      />
      {isLoading ? (
        <p className="text-slate-500">Lade…</p>
      ) : (
        <>
          <EmailTable items={data?.items ?? []} />
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between text-sm text-slate-600">
              <span>
                Seite {data.page} von {data.pages} ({data.total} gesamt)
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="rounded border px-3 py-1 disabled:opacity-40"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Zurück
                </button>
                <button
                  type="button"
                  className="rounded border px-3 py-1 disabled:opacity-40"
                  disabled={page >= data.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Weiter
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
