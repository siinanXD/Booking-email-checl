import { Button } from "@/shared/ui/Button";
import type { Provider } from "./types";

type Props = {
  provider: Provider;
  onProviderChange: (provider: Provider) => void;
  onContinue: () => void;
};

export function ProviderStep({ provider, onProviderChange, onContinue }: Props) {
  return (
    <div className="mt-6 space-y-4">
      <div className="space-y-2">
        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 p-3">
          <input
            type="radio"
            checked={provider === "imap"}
            onChange={() => onProviderChange("imap")}
          />
          <span>
            <span className="font-medium">IMAP</span>
            <span className="block text-xs text-slate-500">
              GMX, Web.de, Gmail, eigener Server
            </span>
          </span>
        </label>
        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 p-3">
          <input
            type="radio"
            checked={provider === "outlook"}
            onChange={() => onProviderChange("outlook")}
          />
          <span>
            <span className="font-medium">Microsoft Outlook</span>
            <span className="block text-xs text-slate-500">
              Graph API (Azure-App in .env konfiguriert)
            </span>
          </span>
        </label>
      </div>
      <Button className="w-full" onClick={onContinue}>
        Weiter
      </Button>
    </div>
  );
}
