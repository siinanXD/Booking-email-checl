import { Server, Cloud } from "lucide-react";
import { Button } from "@/shared/ui/Button";
import type { Provider } from "./types";

type Props = {
  provider: Provider;
  onProviderChange: (provider: Provider) => void;
  onContinue: () => void;
};

const OPTIONS: {
  id: Provider;
  icon: typeof Server;
  title: string;
  description: string;
}[] = [
  {
    id: "imap",
    icon: Server,
    title: "IMAP",
    description: "GMX, Web.de, Gmail, eigener Server",
  },
  {
    id: "outlook",
    icon: Cloud,
    title: "Microsoft Outlook",
    description: "Graph API (Azure-App in .env konfiguriert)",
  },
];

export function ProviderStep({ provider, onProviderChange, onContinue }: Props) {
  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-semibold text-white">E-Mail-Anbieter wählen</p>
        <p className="mt-0.5 text-xs text-slate-400">Welcher Dienst soll verbunden werden?</p>
      </div>
      <div className="space-y-2">
        {OPTIONS.map(({ id, icon: Icon, title, description }) => (
          <label
            key={id}
            className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 transition-all ${
              provider === id
                ? "border-indigo-500/60 bg-indigo-500/10 ring-1 ring-indigo-500/30"
                : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/8"
            }`}
          >
            <input
              type="radio"
              className="sr-only"
              checked={provider === id}
              onChange={() => onProviderChange(id)}
            />
            <div
              className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${
                provider === id ? "bg-indigo-500/20 text-indigo-400" : "bg-white/10 text-slate-400"
              }`}
            >
              <Icon size={18} />
            </div>
            <div>
              <p className={`text-sm font-medium ${provider === id ? "text-white" : "text-slate-300"}`}>
                {title}
              </p>
              <p className="text-xs text-slate-500">{description}</p>
            </div>
            <div className="ml-auto">
              <div
                className={`h-4 w-4 rounded-full border-2 transition-all ${
                  provider === id
                    ? "border-indigo-500 bg-indigo-500"
                    : "border-slate-600 bg-transparent"
                }`}
              />
            </div>
          </label>
        ))}
      </div>
      <Button className="w-full py-2.5" onClick={onContinue}>
        Weiter
      </Button>
    </div>
  );
}
