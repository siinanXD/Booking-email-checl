import { apiClient } from "@/lib/api/client";
import type { CostsResponse } from "@/lib/types/api";

export async function fetchCosts(
  fromDate?: string,
  toDate?: string,
  groupBy = "day"
): Promise<CostsResponse> {
  const { data } = await apiClient.get<CostsResponse>("/api/costs/", {
    params: { from_date: fromDate, to_date: toDate, group_by: groupBy },
  });
  return data;
}
