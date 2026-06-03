import { Card } from "@/shared/ui/Card";

export function AdminDiagnosticsPage() {
  return (
    <Card className="space-y-2">
      <h2 className="text-lg font-medium text-slate-900">Diagnose</h2>
      <p className="text-sm text-slate-600">
        Mail- und WhatsApp-Verbindungstests pro Mandant kommen in Phase 2.
      </p>
    </Card>
  );
}
