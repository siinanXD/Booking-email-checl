export type Provider = "imap" | "outlook";
export type Step = "provider" | "config" | "test";

export function isAccountAdmin(role: string | undefined): boolean {
  return role === "owner" || role === "admin" || role === "platform_admin";
}
