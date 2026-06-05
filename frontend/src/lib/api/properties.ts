import { apiClient } from "@/lib/api/client";
import type { PropertyRecipientItem } from "@/lib/types/api";

export type PropertyHistoryItem = {
  correlation_id: string;
  subject: string;
  received_at: string | null;
  intent: string | null;
  booking_number: string | null;
  property_name: string | null;
};

export type PropertySuggestion = {
  property_name: string;
  mail_count: number;
};

export async function fetchPropertyHistory(params?: {
  property_name?: string;
  limit?: number;
}): Promise<{ items: PropertyHistoryItem[]; total: number }> {
  const { data } = await apiClient.get("/api/properties/history", { params });
  return data;
}

export async function fetchPropertyRecipients(): Promise<{
  items: PropertyRecipientItem[];
}> {
  const { data } = await apiClient.get("/api/properties/recipients");
  return data;
}

export async function savePropertyRecipients(
  items: PropertyRecipientItem[]
): Promise<{ items: PropertyRecipientItem[] }> {
  const { data } = await apiClient.put("/api/properties/recipients", { items });
  return data;
}

export async function fetchPropertySuggestions(limit = 20): Promise<{
  items: PropertySuggestion[];
}> {
  const { data } = await apiClient.get("/api/properties/suggestions", {
    params: { limit },
  });
  return data;
}
