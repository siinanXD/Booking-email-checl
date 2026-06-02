import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/features/auth/authStore";
import { useAuthHydrated } from "@/features/auth/useAuthHydrated";

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
  const hydrated = useAuthHydrated();
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const loadUser = useAuthStore((s) => s.loadUser);
  const location = useLocation();

  useEffect(() => {
    if (hydrated) {
      void loadUser();
    }
  }, [hydrated, loadUser]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100 text-slate-500">
        Lade…
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  if (needsMailOnboarding(user) && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
