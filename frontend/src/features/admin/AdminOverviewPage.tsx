import { Card } from "@/shared/ui/Card";

export function AdminOverviewPage() {
  return (
    <Card className="space-y-2">
      <h2 className="text-lg font-medium text-slate-900">Plattform-Übersicht</h2>
      <p className="text-sm text-slate-600">
        KPIs und Mandanten-Aktivität folgen in Phase 3. Nutze bis dahin den Tab
        „Mandanten“ für Freischaltungen.
      </p>
    </Card>
  );
}
