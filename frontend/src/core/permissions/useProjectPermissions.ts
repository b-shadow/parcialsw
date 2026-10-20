import { useEffect, useCallback } from "react";
import { create } from "zustand";
import { apiClient } from "../api/client";
import type { MyMembership, PermissionCode, ProjectRole } from "../contracts/mejoras2p";

interface ProjectPermissionsCache {
  role: ProjectRole | null;
  permissions: PermissionCode[];
  timestamp: number;
  loading: boolean;
  error: unknown | null;
}

interface PermissionsStoreState {
  cache: Record<string, ProjectPermissionsCache>;
  inFlight: Record<string, Promise<MyMembership> | undefined>;
  fetchPermissions: (projectId: string, force?: boolean) => Promise<void>;
  invalidate: (projectId?: string) => void;
}

const CACHE_TTL_MS = 60_000;

export const usePermissionsStore = create<PermissionsStoreState>((set, get) => ({
  cache: {},
  inFlight: {},

  fetchPermissions: async (projectId: string, force = false) => {
    if (!projectId) return;

    const state = get();
    const existing = state.cache[projectId];
    const now = Date.now();

    if (!force && existing && now - existing.timestamp < CACHE_TTL_MS && !existing.error) {
      return;
    }

    const currentFlight = state.inFlight[projectId];
    if (currentFlight) {
      await currentFlight;
      return;
    }

    set((s) => ({
      cache: {
        ...s.cache,
        [projectId]: {
          role: s.cache[projectId]?.role ?? null,
          permissions: s.cache[projectId]?.permissions ?? [],
          timestamp: s.cache[projectId]?.timestamp ?? 0,
          loading: true,
          error: null,
        },
      },
    }));

    const flight = (async () => {
      try {
        const response = await apiClient.get<MyMembership>(`/projects/${projectId}/members/me`);
        const data = response.data;
        set((s) => ({
          cache: {
            ...s.cache,
            [projectId]: {
              role: data.project_role,
              permissions: data.permissions,
              timestamp: Date.now(),
              loading: false,
              error: null,
            },
          },
        }));
        return data;
      } catch (err) {
        set((s) => ({
          cache: {
            ...s.cache,
            [projectId]: {
              role: null,
              permissions: [],
              timestamp: 0,
              loading: false,
              error: err,
            },
          },
        }));
        throw err;
      } finally {
        set((s) => {
          const nextInFlight = { ...s.inFlight };
          delete nextInFlight[projectId];
          return { inFlight: nextInFlight };
        });
      }
    })();

    set((s) => ({
      inFlight: {
        ...s.inFlight,
        [projectId]: flight,
      },
    }));

    try {
      await flight;
    } catch {
      // Handled in cache state
    }
  },

  invalidate: (projectId?: string) => {
    if (projectId) {
      set((s) => {
        const nextCache = { ...s.cache };
        delete nextCache[projectId];
        return { cache: nextCache };
      });
    } else {
      set({ cache: {}, inFlight: {} });
    }
  },
}));

export function useProjectPermissions(projectId?: string): {
  role: ProjectRole | null;
  can: (code: PermissionCode) => boolean;
  loading: boolean;
  refresh: () => Promise<void>;
} {
  const cacheEntry = usePermissionsStore((s) => (projectId ? s.cache[projectId] : undefined));
  const fetchPermissions = usePermissionsStore((s) => s.fetchPermissions);

  useEffect(() => {
    if (projectId) {
      void fetchPermissions(projectId);
    }
  }, [projectId, fetchPermissions]);

  const refresh = useCallback(async () => {
    if (projectId) {
      await fetchPermissions(projectId, true);
    }
  }, [projectId, fetchPermissions]);

  const loading = projectId ? (cacheEntry?.loading ?? true) : false;
  const role = cacheEntry?.role ?? null;
  const permissions = cacheEntry?.permissions ?? [];

  const can = useCallback(
    (code: PermissionCode): boolean => {
      if (!projectId || loading) {
        return false;
      }
      return permissions.includes(code);
    },
    [projectId, loading, permissions]
  );

  return {
    role,
    can,
    loading,
    refresh,
  };
}
