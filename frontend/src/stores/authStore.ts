import { create } from "zustand";
import { persist } from "zustand/middleware";
import { fetchMe, login as loginApi, logoutApi } from "@/api/auth";
import type { UserResponse } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserResponse | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: () => Boolean(get().accessToken),
      login: async (email, password) => {
        const tokens = await loginApi(email, password);
        set({
          accessToken: tokens.access_token,
          refreshToken: tokens.refresh_token,
        });
        const user = await fetchMe();
        set({ user });
      },
      logout: () => {
        const token = get().accessToken;
        if (token) {
          logoutApi().catch(() => undefined);
        }
        set({ accessToken: null, refreshToken: null, user: null });
      },
      loadUser: async () => {
        if (!get().accessToken) return;
        try {
          const user = await fetchMe();
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
