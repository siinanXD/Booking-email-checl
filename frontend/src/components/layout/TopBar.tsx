import { LogOut, User } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/Button";

export function TopBar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
      <h1 className="text-lg font-semibold text-slate-800">AI Mail Platform</h1>
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-2 text-sm text-slate-600">
          <User size={16} />
          {user?.email ?? "—"}
        </span>
        <Button variant="ghost" onClick={logout} title="Abmelden">
          <LogOut size={18} />
        </Button>
      </div>
    </header>
  );
}
