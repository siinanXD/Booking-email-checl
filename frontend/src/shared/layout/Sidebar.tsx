import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  CalendarCheck,
  XCircle,
  RefreshCw,
  MessageSquare,
  ClipboardCheck,
  DollarSign,
  Building2,
  Shield,
  Users,
  Stethoscope,
  LineChart,
  SlidersHorizontal,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "@/lib/api/dashboard";
import { fetchPendingAccounts } from "@/lib/api/admin";
import { useAuthStore } from "@/features/auth/authStore";

const tenantLinks = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/bookings", label: "Buchungen", icon: CalendarCheck },
  { to: "/cancellations", label: "Stornos", icon: XCircle },
  { to: "/changes", label: "Änderungen", icon: RefreshCw },
  { to: "/messages", label: "Nachrichten", icon: MessageSquare },
  { to: "/properties", label: "Unterkünfte", icon: Building2 },
  { to: "/review", label: "Review", icon: ClipboardCheck, badge: true },
  { to: "/costs", label: "API-Kosten", icon: DollarSign },
];

const adminLinks = [
  { to: "/admin/overview", label: "Übersicht", icon: Shield },
  { to: "/admin/accounts", label: "Mandanten", icon: Users, badge: true },
  { to: "/admin/diagnostics", label: "Diagnose", icon: Stethoscope },
  { to: "/admin/observability", label: "Observability", icon: LineChart },
  { to: "/admin/llm-config", label: "LLM-Konfiguration", icon: SlidersHorizontal },
];

export function Sidebar() {
  const isPlatformAdmin = useAuthStore((s) => s.isPlatformAdmin());
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 30_000,
    enabled: !isPlatformAdmin,
  });
  const { data: pendingAccounts } = useQuery({
    queryKey: ["admin-accounts", "pending-count"],
    queryFn: fetchPendingAccounts,
    enabled: isPlatformAdmin,
    refetchInterval: 60_000,
  });
  const pending = stats?.pending_review ?? 0;
  const pendingApprovals = pendingAccounts?.total ?? 0;
  const links = isPlatformAdmin ? adminLinks : tenantLinks;

  return (
    <aside className="flex w-56 flex-col bg-slate-900 text-slate-200">
      <div className="border-b border-slate-700 px-4 py-5">
        <p className="text-xs uppercase tracking-wide text-slate-400">
          AI Mail
        </p>
        <p className="font-semibold text-white">
          {isPlatformAdmin ? "Plattform" : "Platform"}
        </p>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {links.map(({ to, label, icon: Icon, badge }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/" || to === "/admin/overview"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                isActive
                  ? "bg-indigo-600 text-white"
                  : "text-slate-300 hover:bg-slate-800"
              }`
            }
          >
            <Icon size={18} />
            <span className="flex-1">{label}</span>
            {badge && !isPlatformAdmin && pending > 0 && (
              <span className="animate-pulse rounded-full bg-red-500 px-2 py-0.5 text-xs font-bold text-white">
                {pending}
              </span>
            )}
            {badge && isPlatformAdmin && pendingApprovals > 0 && (
              <span className="rounded-full bg-amber-500 px-2 py-0.5 text-xs font-bold text-white">
                {pendingApprovals}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
