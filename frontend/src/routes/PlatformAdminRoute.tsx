import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

export function PlatformAdminRoute() {
  const isPlatformAdmin = useAuthStore((s) => s.isPlatformAdmin);

  if (!isPlatformAdmin()) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
