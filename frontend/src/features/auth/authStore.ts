import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  fetchMe,
  login as loginApi,
  logoutApi,
  register as registerApi,
} from "@/lib/api/auth";
import type { RegisterRequest, RegisterResponse, UserResponse } from "@/lib/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserResponse | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<RegisterResponse>;
  logout: () => void;
  loadUser: () => Promise<void>;
  isAuthenticated: () => boolean;
  isPlatformAdmin: () => boolean;
  isAccountAdmin: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: () =>
        Boolean(get().accessToken && get().user),
      isPlatformAdmin: () => get().user?.role === "platform_admin",
      isAccountAdmin: () => {
        const role = get().user?.role;
        return role === "owner" || role === "admin" || role === "platform_admin";
      },
      login: async (email, password) => {
        const tokens = await loginApi(email, password);
        try {
          const user = await fetchMe(tokens.access_token);
          set({
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            user,
          });
        } catch (err) {
          set({ accessToken: null, refreshToken: null, user: null });
          throw err;
        }
      },
      register: async (payload) => registerApi(payload),
      logout: () => {
        const token = get().accessToken;
        if (token) {
          logoutApi().catch(() => undefined);
        }
        set({ accessToken: null, refreshToken: null, user: null });
      },
      loadUser: async () => {
        const token = get().accessToken;
        if (!token) return;
        try {
          const user = await fetchMe(token);
          set({ user });
        } catch {
          get().logout();
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        user: s.user,
      }),
    }
  )
);
