import { apiClient } from "@/lib/api/client";
import type { MailConnectionResponse, MailTestResponse } from "@/lib/types/api";

export async function fetchMailConnection(): Promise<MailConnectionResponse> {
  const { data } = await apiClient.get<MailConnectionResponse>(
    "/api/mail/connection"
  );
  return data;
}

export async function saveMailConnection(
  payload: Partial<MailConnectionResponse> & {
    imap_password?: string;
    onboarding_completed?: boolean;
  }
): Promise<MailConnectionResponse> {
  const { data } = await apiClient.put<MailConnectionResponse>(
    "/api/mail/connection",
    payload
  );
  return data;
}

export async function testMailConnection(): Promise<MailTestResponse> {
  const { data } = await apiClient.post<MailTestResponse>("/api/mail/test");
  return data;
}
