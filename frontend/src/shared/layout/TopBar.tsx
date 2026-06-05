import { Link } from "react-router-dom";
import { LogOut, Settings, ChevronDown } from "lucide-react";
import { useAuthStore } from "@/features/auth/authStore";

function getInitials(email: string): string {
  const parts = email.split("@")[0].split(/[._-]/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return email.slice(0, 2).toUpperCase();
}

export function TopBar() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const isPlatformAdmin = useAuthStore((s) => s.isPlatformAdmin());
  const profileLink = isPlatformAdmin ? "/admin/overview" : "/settings";
  const initials = user?.email ? getInitials(user.email) : "??";

  return (
    <header className="flex h-14 flex-shrink-0 items-center justify-between border-b border-slate-200/80 bg-white/90 px-6 backdrop-blur-sm">
      <div className="flex items-center gap-2">
        <h1 className="text-sm font-semibold text-slate-700">
          {isPlatformAdmin ? "Plattform-Administration" : "AI Mail Platform"}
        </h1>
      </div>

      <div className="flex items-center gap-1">
        {/* User menu */}
        <Link
          to={profileLink}
          className="group flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors hover:bg-slate-100"
          title="Einstellungen"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700">
            {initials}
          </div>
          <span className="max-w-[160px] truncate text-sm text-slate-600 group-hover:text-slate-900">
            {user?.email ?? "—"}
          </span>
          <ChevronDown size={13} className="text-slate-400 transition-transform group-hover:text-slate-600" />
        </Link>

        <div className="mx-1 h-5 w-px bg-slate-200" />

        {/* Settings shortcut */}
        <Link
          to={profileLink}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
          title="Einstellungen öffnen"
        >
          <Settings size={16} />
        </Link>

        {/* Logout */}
        <button
          type="button"
          onClick={logout}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
          title="Abmelden"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
