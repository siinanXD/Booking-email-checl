import { apiClient } from "@/lib/api/client";
import type {
  MailConnectionResponse,
  MailSyncResponse,
  MailTestResponse,
} from "@/lib/types/api";

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

export async function syncMailConnection(
  options?: { reprocess?: boolean },
): Promise<MailSyncResponse> {
  const params =
    options?.reprocess === false ? undefined : { reprocess: "1" as const };
  const { data } = await apiClient.post<MailSyncResponse>(
    "/api/mail/sync",
    null,
    { params }
  );
  return data;
}

export interface AutodiscoverResult {
  preset_id: string;
  label?: string;
  host?: string;
  port?: number;
  use_ssl?: boolean;
  source: "local" | "ispdb" | "unknown";
}

export async function autodiscoverImap(
  domain: string
): Promise<AutodiscoverResult | null> {
  try {
    const { data } = await apiClient.get<AutodiscoverResult>(
      "/api/mail/autodiscover",
      { params: { domain } }
    );
    return data;
  } catch {
    return null;
  }
}

export async function fetchOutlookAuthorizeUrl(
  returnTo = "/onboarding",
  frontendOrigin?: string
): Promise<string> {
  const { data } = await apiClient.get<{ authorize_url: string }>(
    "/api/mail/outlook/authorize-url",
    {
      params: {
        return_to: returnTo,
        frontend_origin: frontendOrigin ?? window.location.origin,
      },
    }
  );
  return data.authorize_url;
}
