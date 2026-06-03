import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/features/auth/authStore";

/** Mandanten-Routen — Plattform-Admins werden zur Admin-Konsole geleitet. */
export function TenantRoute() {
  const isPlatformAdmin = useAuthStore((s) => s.isPlatformAdmin());

  if (isPlatformAdmin) {
    return <Navigate to="/admin/overview" replace />;
  }

  return <Outlet />;
}
