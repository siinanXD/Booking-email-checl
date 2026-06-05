import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  CalendarCheck,
  XCircle,
  RefreshCw,
  MessageSquare,
  ClipboardCheck,
  AlertTriangle,
  CheckCircle2,
  Building2,
  Shield,
  Users,
  Stethoscope,
  LineChart,
  SlidersHorizontal,
  GitBranch,
  Tag,
  LifeBuoy,
  Ticket,
  Zap,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardStats } from "@/lib/api/dashboard";
import { fetchPendingAccounts } from "@/lib/api/admin";
import { fetchWorkflowNav } from "@/lib/api/workflows";
import { useAuthStore } from "@/features/auth/authStore";

type NavCountKey =
  | "nav_bookings"
  | "nav_cancellations"
  | "nav_changes"
  | "nav_messages"
  | "nav_ground_zero"
  | "nav_completed";

type SidebarLink = {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  badge?: boolean;
  navCountKey?: NavCountKey;
};

const tenantLinks: SidebarLink[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  {
    to: "/bookings",
    label: "Buchungen",
    icon: CalendarCheck,
    navCountKey: "nav_bookings",
  },
  {
    to: "/cancellations",
    label: "Stornos",
    icon: XCircle,
    navCountKey: "nav_cancellations",
  },
  {
    to: "/changes",
    label: "Änderungen",
    icon: RefreshCw,
    navCountKey: "nav_changes",
  },
  {
    to: "/messages",
    label: "Nachrichten",
    icon: MessageSquare,
    navCountKey: "nav_messages",
  },
  { to: "/properties", label: "Unterkünfte", icon: Building2 },
  { to: "/support", label: "Support", icon: LifeBuoy },
  { to: "/review", label: "Review", icon: ClipboardCheck, badge: true },
  {
    to: "/ground-zero",
    label: "Ground Zero",
    icon: AlertTriangle,
    navCountKey: "nav_ground_zero",
  },
  {
    to: "/completed",
    label: "Abgeschlossen",
    icon: CheckCircle2,
    navCountKey: "nav_completed",
  },
];

const adminLinks: SidebarLink[] = [
  { to: "/admin/overview", label: "Übersicht", icon: Shield },
  { to: "/admin/accounts", label: "Mandanten", icon: Users, badge: true },
  { to: "/admin/diagnostics", label: "Diagnose", icon: Stethoscope },
  { to: "/admin/observability", label: "Observability", icon: LineChart },
  { to: "/admin/tickets", label: "Tickets", icon: Ticket },
  { to: "/admin/llm-config", label: "LLM-Konfiguration", icon: SlidersHorizontal },
  { to: "/admin/workflows", label: "Workflows", icon: GitBranch },
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
  const { data: workflowNav } = useQuery({
    queryKey: ["workflows", "nav"],
    queryFn: fetchWorkflowNav,
    enabled: !isPlatformAdmin,
    refetchInterval: 60_000,
  });
  const pending = stats?.pending_review ?? 0;
  const pendingApprovals = pendingAccounts?.total ?? 0;
  const workflowRubrics: SidebarLink[] = (workflowNav?.items ?? []).map((wf) => ({
    to: `/rubrics/${wf.slug}`,
    label: wf.label,
    icon: Tag,
  }));
  const links = isPlatformAdmin
    ? adminLinks
    : [
        ...tenantLinks.slice(0, 8),
        ...workflowRubrics,
        ...tenantLinks.slice(8),
      ];

  return (
    <aside
      className="flex w-56 flex-col overflow-hidden"
      style={{ background: "linear-gradient(180deg, #0b1120 0%, #111827 100%)" }}
    >
      {/* Logo / Brand */}
      <div className="flex items-center gap-2.5 border-b border-white/[0.07] px-4 py-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20">
          <Zap size={14} className="text-indigo-400" />
        </div>
        <div>
          <p className="text-[11px] font-medium uppercase tracking-widest text-slate-500">
            AI Mail
          </p>
          <p className="text-sm font-semibold leading-tight text-white">
            {isPlatformAdmin ? "Plattform" : "Platform"}
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <div className="space-y-0.5">
          {links.map(({ to, label, icon: Icon, badge, navCountKey }) => {
            const navCount =
              navCountKey && stats
                ? (stats[navCountKey] as number | undefined)
                : undefined;
            return (
              <NavLink
                key={to}
                to={to}
                end={to === "/" || to === "/admin/overview"}
                className={({ isActive }) =>
                  `group flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-indigo-600/90 text-white shadow-sm"
                      : "text-slate-400 hover:bg-white/[0.06] hover:text-slate-200"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      size={16}
                      className={`flex-shrink-0 transition-colors ${
                        isActive ? "text-white" : "text-slate-500 group-hover:text-slate-300"
                      }`}
                    />
                    <span className="flex-1 truncate">{label}</span>
                    {navCountKey && navCount != null && navCount > 0 && (
                      <span
                        className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold tabular-nums ${
                          isActive
                            ? "bg-white/20 text-white"
                            : "bg-slate-700 text-slate-300"
                        }`}
                      >
                        {navCount}
                      </span>
                    )}
                    {badge && !isPlatformAdmin && pending > 0 && (
                      <span className="animate-pulse-soft rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                        {pending}
                      </span>
                    )}
                    {badge && isPlatformAdmin && pendingApprovals > 0 && (
                      <span className="rounded-full bg-amber-500 px-1.5 py-0.5 text-[10px] font-bold text-white">
                        {pendingApprovals}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t border-white/[0.07] px-3 py-3">
        <div className="flex items-center gap-2 rounded-lg px-2 py-1.5">
          <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-400">
            AI
          </div>
          <span className="truncate text-[11px] text-slate-500">v1.0 · AI Mail</span>
        </div>
      </div>
    </aside>
  );
}
