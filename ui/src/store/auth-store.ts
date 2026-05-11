import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { Role, UserPublic } from "@/types/api";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserPublic | null;
  hydrated: boolean;
  setTokens: (access: string, refresh: string) => void;
  setUser: (u: UserPublic | null) => void;
  clear: () => void;
  hasRole: (role: Role) => boolean;
  hasAnyRole: (roles: Role[]) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      hydrated: false,
      setTokens: (access, refresh) =>
        set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null }),
      hasRole: (role) => !!get().user?.roles.includes(role),
      hasAnyRole: (roles) =>
        !!get().user?.roles.some((r) => roles.includes(r as Role)),
    }),
    {
      name: "sep.auth",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? window.localStorage : (undefined as any),
      ),
      partialize: (s) => ({
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        user: s.user,
      }),
      onRehydrateStorage: () => (state) => {
        state && (state.hydrated = true);
      },
    },
  ),
);
