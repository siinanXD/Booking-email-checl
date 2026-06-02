import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

function needsMailOnboarding(user: {
  role?: string;
  account_status?: string | null;
  mail_onboarding_completed?: boolean | null;
} | null): boolean {
  if (!user) return false;
  const isAdmin =
    user.role === "owner" ||
    user.role === "admin" ||
    user.role === "platform_admin";
  if (!isAdmin) return false;
  if (user.account_status !== "active") return false;
  return user.mail_onboarding_completed !== true;
}

export function ProtectedRoute() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const loadUser = useAuthStore((s) => s.loadUser);
  const location = useLocation();

  useEffect(() => {
    void loadUser();
  }, [loadUser]);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  if (needsMailOnboarding(user) && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
