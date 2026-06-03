/** Mail-Onboarding nur für Mandanten-Admins (nicht Plattform-Admin). */

export function needsMailOnboarding(user: {
  role?: string;
  account_status?: string | null;
  mail_onboarding_completed?: boolean | null;
} | null): boolean {
  if (!user) return false;
  if (user.role === "platform_admin") return false;
  const isAdmin = user.role === "owner" || user.role === "admin";
  if (!isAdmin) return false;
  if (user.account_status !== "active") return false;
  return user.mail_onboarding_completed !== true;
}
