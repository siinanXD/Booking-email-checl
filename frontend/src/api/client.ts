import axios from "axios";
import { useAuthStore } from "@/stores/authStore";

const baseURL = import.meta.env.VITE_API_URL ?? "";

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const url = err.config?.url ?? "";
      const isAuthEndpoint =
        url.includes("/api/auth/login") ||
        url.includes("/api/auth/register") ||
        url.includes("/api/auth/refresh");
      if (!isAuthEndpoint) {
        useAuthStore.getState().logout();
      }
    }
    return Promise.reject(err);
  }
);
