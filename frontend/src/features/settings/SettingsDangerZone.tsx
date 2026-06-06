import { TriangleAlert, Trash2 } from "lucide-react";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";

export interface SettingsDangerZoneProps {
  wipeConfirm: string;
  onWipeConfirmChange: (value: string) => void;
  onWipe: () => void;
  wipePending: boolean;
}

export function SettingsDangerZone({
  wipeConfirm,
  onWipeConfirmChange,
  onWipe,
  wipePending,
}: SettingsDangerZoneProps) {
  const confirmed = wipeConfirm === "ALLE DATEN LOESCHEN";

  return (
    <div className="rounded-xl border border-red-200/80 bg-red-50/50 p-5 space-y-4">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-red-100 text-red-600">
          <TriangleAlert size={16} />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-red-800">Gefahrenzone</h3>
          <p className="mt-0.5 text-xs text-red-600">
            Löscht alle E-Mails, Reviews, Metriken und gespeicherten Einstellungen.
            Login-Benutzer bleiben erhalten.
          </p>
        </div>
      </div>
      <div className="space-y-2">
        <label className="block text-xs font-medium text-red-700">
          Tippe zur Bestätigung: <code className="rounded bg-red-100 px-1">ALLE DATEN LOESCHEN</code>
        </label>
        <Input
          value={wipeConfirm}
          onChange={(e) => onWipeConfirmChange(e.target.value)}
          placeholder="ALLE DATEN LOESCHEN"
          className="border-red-200 bg-white focus:border-red-400 focus:ring-red-100"
        />
      </div>
      <Button
        variant="danger"
        size="sm"
        disabled={!confirmed || wipePending}
        onClick={onWipe}
      >
        <Trash2 size={14} />
        {wipePending ? "Wird gelöscht…" : "Alle Daten löschen"}
      </Button>
    </div>
  );
}
