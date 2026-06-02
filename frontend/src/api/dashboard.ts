import { apiClient } from "@/api/client";
import type { DashboardStats } from "@/types/api";

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/api/dashboard/stats");
  return data;
}
