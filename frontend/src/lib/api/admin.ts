import { apiClient } from "@/lib/api/client";
import type {
  AccountListResponse,
  AdminMeResponse,
  AdminWhatsAppInfoResponse,
  AdminWhatsAppTestResponse,
  AdminWhatsAppTestTemplate,
  MailConnectionResponse,
  MailTestResponse,
} from "@/lib/types/api";

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

export async function fetchAccountMailConnection(
  accountId: string
): Promise<MailConnectionResponse> {
  const { data } = await apiClient.get<MailConnectionResponse>(
    `/api/admin/accounts/${accountId}/mail/connection`
  );
  return data;
}

export async function testAccountMailConnection(
  accountId: string
): Promise<MailTestResponse> {
  const { data } = await apiClient.post<MailTestResponse>(
    `/api/admin/accounts/${accountId}/mail/test`
  );
  return data;
}

export async function fetchAccountWhatsAppInfo(
  accountId: string
): Promise<AdminWhatsAppInfoResponse> {
  const { data } = await apiClient.get<AdminWhatsAppInfoResponse>(
    `/api/admin/accounts/${accountId}/whatsapp`
  );
  return data;
}

export async function testAccountWhatsApp(
  accountId: string,
  payload: {
    recipient_e164?: string;
    template?: AdminWhatsAppTestTemplate;
  }
): Promise<AdminWhatsAppTestResponse> {
  const { data } = await apiClient.post<AdminWhatsAppTestResponse>(
    `/api/admin/accounts/${accountId}/whatsapp/test`,
    payload
  );
  return data;
}
