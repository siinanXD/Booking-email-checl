import { apiClient } from "@/api/client";
import type { TokenResponse, UserResponse } from "@/types/api";

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/api/auth/login", {
    email,
    password,
  });
  return data;
}

export async function fetchMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>("/api/auth/me");
  return data;
}

export async function logoutApi(): Promise<void> {
  await apiClient.post("/api/auth/logout");
}
