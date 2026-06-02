import { apiClient } from "@/api/client";

export async function approveReview(
  correlationId: string,
  approvedBody?: string
): Promise<void> {
  await apiClient.post("/api/review/approve", {
    correlation_id: correlationId,
    approved_body: approvedBody,
  });
}

export async function rejectReview(
  correlationId: string,
  reason: string
): Promise<void> {
  await apiClient.post("/api/review/reject", {
    correlation_id: correlationId,
    reason,
  });
}
