import { apiClient } from "@/lib/api/client";
import type { AccountListResponse, AdminMeResponse } from "@/lib/types/api";

export async function fetchAdminMe(): Promise<AdminMeResponse> {
  const { data } = await apiClient.get<AdminMeResponse>("/api/admin/me");
  return data;
}

export async function fetchPendingAccounts(): Promise<AccountListResponse> {
  const { data } = await apiClient.get<AccountListResponse>(
    "/api/admin/accounts?status=pending"
  );
  return data;
}

export async function fetchAllAccounts(): Promise<AccountListResponse> {
  const { data } = await apiClient.get<AccountListResponse>(
    "/api/admin/accounts"
  );
  return data;
}

export async function approveAccount(accountId: string): Promise<void> {
  await apiClient.post(`/api/admin/accounts/${accountId}/approve`);
}

export async function rejectAccount(
  accountId: string,
  reason?: string
): Promise<void> {
  await apiClient.post(`/api/admin/accounts/${accountId}/reject`, {
    reason: reason ?? null,
  });
}
