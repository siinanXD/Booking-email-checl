import { useEffect, useState } from "react";
import { useAuthStore } from "@/features/auth/authStore";

/** Wartet auf Zustand-Persist-Rehydration (wichtig nach OAuth-Redirect). */
export function useAuthHydrated(): boolean {
  const [hydrated, setHydrated] = useState(() =>
    useAuthStore.persist.hasHydrated()
  );

  useEffect(() => {
    if (useAuthStore.persist.hasHydrated()) {
      setHydrated(true);
      return;
    }
    return useAuthStore.persist.onFinishHydration(() => setHydrated(true));
  }, []);

  return hydrated;
}
