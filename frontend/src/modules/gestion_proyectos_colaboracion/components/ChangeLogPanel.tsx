import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle, Database, History, LoaderCircle } from "lucide-react";

import type { ChangeLogEntry, ChangeLogPage } from "../../../core/contracts/mejoras2p";
import { ProjectSocketClient, type ParsedProjectSocketEvent } from "../../../core/websocket/projectSocket";
import { Avatar } from "../../../shared/components/Avatar";
import { EmptyState } from "../../../shared/components/EmptyState";
import { Skeleton } from "../../../shared/components/Skeleton";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { changeLogService } from "../services/changeLogService";
import { projectService } from "../services/projectService";
import type { ProjectMember } from "../types/project";

export function formatRelativeTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    const now = new Date();
    const diffInSeconds = Math.round((date.getTime() - now.getTime()) / 1000);
    const diffInMinutes = Math.round(diffInSeconds / 60);
    const diffInHours = Math.round(diffInMinutes / 60);
    const diffInDays = Math.round(diffInHours / 24);

    const rtf = new Intl.RelativeTimeFormat("es", { numeric: "auto" });

    if (Math.abs(diffInSeconds) < 60) {
      return "hace un momento";
    }
    if (Math.abs(diffInMinutes) < 60) {
      return rtf.format(diffInMinutes, "minutes");
    }
    if (Math.abs(diffInHours) < 24) {
      return rtf.format(diffInHours, "hours");
    }
    if (Math.abs(diffInDays) < 7) {
      return rtf.format(diffInDays, "days");
    }
    return date.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
  } catch {
    return dateString;
  }
}

export function getDayLabel(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Otros";
    const now = new Date();

    const isToday =
      date.getDate() === now.getDate() &&
      date.getMonth() === now.getMonth() &&
      date.getFullYear() === now.getFullYear();

    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    const isYesterday =
      date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear();

    if (isToday) return "Hoy";
    if (isYesterday) return "Ayer";
    return date.toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return "Otros";
  }
}

type KindFilter = "" | "clase" | "rel" | "ia" | "ver" | "gen";

const KIND_FILTERS: { id: KindFilter; label: string; entityType?: string }[] = [
  { id: "", label: "Todo" },
  { id: "clase", label: "Clases", entityType: "class" },
  { id: "rel", label: "Relaciones", entityType: "relationship" },
  { id: "ia", label: "IA", entityType: "ai_action" },
  { id: "ver", label: "Versiones", entityType: "version" },
  { id: "gen", label: "Generación", entityType: "generation" },
];

function getEntryBadge(entry: ChangeLogEntry) {
  if (entry.source === "ai") {
    return <StatusBadge tone="ai">IA</StatusBadge>;
  }
  const entity = (entry.entity_type || "").toLowerCase();
  const action = (entry.action || "").toUpperCase();
  if (entity === "class" || action.includes("CLASS")) {
    return <StatusBadge tone="neutral">Clase</StatusBadge>;
  }
  if (entity === "relationship" || action.includes("RELATION")) {
    return <StatusBadge tone="info">Relación</StatusBadge>;
  }
  if (entity === "version" || action.includes("VERSION")) {
    return <StatusBadge tone="info">Versión</StatusBadge>;
  }
  if (entity === "generation" || action.includes("GENERATE")) {
    return <StatusBadge tone="success">Generación</StatusBadge>;
  }
  return <StatusBadge tone="neutral">{entry.entity_type || "Cambio"}</StatusBadge>;
}

export function ChangeLogPanel({ projectId }: { projectId: string }) {
  const [entries, setEntries] = useState<ChangeLogEntry[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [source, setSource] = useState<"redis" | "postgres_fallback">("redis");
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [selectedActorId, setSelectedActorId] = useState<string>("");
  const [selectedKind, setSelectedKind] = useState<KindFilter>("");

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load project members for filter select
  useEffect(() => {
    let cancelled = false;
    projectService
      .members(projectId)
      .then((data) => {
        if (!cancelled) setMembers(data);
      })
      .catch(() => {
        // Members list is non-critical for the log view
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const fetchPage = useCallback(
    async (cursor?: string) => {
      const activeKind = KIND_FILTERS.find((k) => k.id === selectedKind);
      const params = {
        before_id: cursor,
        actor_id: selectedActorId || undefined,
        entity_type: activeKind?.entityType,
      };
      return await changeLogService.list(projectId, params);
    },
    [projectId, selectedActorId, selectedKind]
  );

  const loadInitial = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const page: ChangeLogPage = await fetchPage();
      setEntries(page.items);
      setNextCursor(page.next_cursor);
      setSource(page.source);
    } catch {
      setError("No se pudo cargar el registro de cambios.");
    } finally {
      setLoading(false);
    }
  }, [fetchPage]);

  useEffect(() => {
    void loadInitial();
  }, [loadInitial]);

  const handleLoadMore = async () => {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await fetchPage(nextCursor);
      setEntries((prev) => {
        const existingIds = new Set(prev.map((e) => e.id));
        const newUnique = page.items.filter((item) => !existingIds.has(item.id));
        return [...prev, ...newUnique];
      });
      setNextCursor(page.next_cursor);
      setSource(page.source);
    } catch {
      setError("No se pudieron cargar más cambios.");
    } finally {
      setLoadingMore(false);
    }
  };

  // WebSocket subscription for live updates
  useEffect(() => {
    const handleEvent = (event: ParsedProjectSocketEvent) => {
      const eventRecord = event as unknown as Record<string, unknown>;
      const rawRecord = eventRecord.raw as Record<string, unknown> | undefined;
      const eventType =
        event.type === "UNKNOWN"
          ? (typeof rawRecord?.type === "string" ? rawRecord.type : "")
          : event.type;

      if (eventType === "CHANGE_LOGGED") {
        const payloadRecord =
          (eventRecord.payload as Record<string, unknown> | undefined) ??
          (rawRecord?.payload as Record<string, unknown> | undefined) ??
          rawRecord ??
          {};
        const item: ChangeLogEntry | null =
          (payloadRecord.entry as ChangeLogEntry | undefined) ??
          (payloadRecord.id && payloadRecord.occurred_at
            ? (payloadRecord as unknown as ChangeLogEntry)
            : null);

        if (item) {
          if (item.project_id && item.project_id !== projectId) return;
          setEntries((prev) => {
            if (prev.some((e) => e.id === item.id)) return prev;
            return [item, ...prev];
          });
        }
        return;
      }

      if (
        eventType === "UML_EVENT" ||
        eventType === "AI_ACTION_STATUS_CHANGED" ||
        (typeof eventType === "string" && eventType.startsWith("PROJECT_VERSION_"))
      ) {
        if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
        debounceTimerRef.current = setTimeout(() => {
          void loadInitial();
        }, 1000);
      }
    };

    const client = new ProjectSocketClient({
      projectId,
      getProjectSequence: () => 0,
      getConversationSequence: () => 0,
      onEvent: handleEvent,
      onStatus: () => {},
    });

    client.connect();

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      client.close();
    };
  }, [projectId, loadInitial]);

  const groupedEntries = useMemo(() => {
    const groups: { day: string; items: ChangeLogEntry[] }[] = [];
    for (const entry of entries) {
      const day = getDayLabel(entry.occurred_at);
      let group = groups.find((g) => g.day === day);
      if (!group) {
        group = { day, items: [] };
        groups.push(group);
      }
      group.items.push(entry);
    }
    return groups;
  }, [entries]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-950">
      <div className="border-b border-slate-200 p-5 dark:border-slate-800">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">Registro de cambios</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Se actualiza en vivo. Filtra por integrante o por tipo de cambio.
        </p>
      </div>

      <div className="p-5">
        {/* Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-2" id="rg-filters">
          <select
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 shadow-xs focus:border-teal-600 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
            id="rg-who"
            aria-label="Integrante"
            value={selectedActorId}
            onChange={(e) => setSelectedActorId(e.target.value)}
          >
            <option value="">Todos los integrantes</option>
            {members.map((member) => (
              <option key={member.id} value={member.user_id}>
                {member.full_name || member.email || member.user_id}
              </option>
            ))}
          </select>

          {KIND_FILTERS.map((filter) => {
            const active = selectedKind === filter.id;
            return (
              <button
                key={filter.id}
                type="button"
                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                  active
                    ? "bg-teal-700 text-white dark:bg-teal-600"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                }`}
                aria-pressed={active}
                data-kind={filter.id}
                onClick={() => setSelectedKind(filter.id)}
              >
                {filter.label}
              </button>
            );
          })}
        </div>

        {/* Fallback Banner */}
        {source === "postgres_fallback" && (
          <div
            className="mb-4 flex items-center gap-2 rounded-md border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200"
            role="alert"
            id="rg-fallback"
          >
            <Database className="shrink-0 text-amber-700 dark:text-amber-400" size={16} />
            <span>
              Registro en modo respaldo: Redis no responde y se muestra la auditoría de PostgreSQL. Los cambios se siguen guardando.
            </span>
          </div>
        )}

        {/* Content States */}
        {loading ? (
          <div className="space-y-3 py-4" aria-live="polite">
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
            <Skeleton className="h-14 w-full" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 rounded-md border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
            <AlertCircle className="shrink-0" size={18} />
            <span>{error}</span>
          </div>
        ) : entries.length === 0 ? (
          <EmptyState
            icon={<History size={24} />}
            title="Sin cambios registrados"
            description="No hay eventos que coincidan con los filtros seleccionados."
          />
        ) : (
          <div className="space-y-6" id="rg-list">
            {groupedEntries.map((group) => (
              <div key={group.day}>
                <div className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  {group.day}
                </div>
                <div className="space-y-4 border-l-2 border-slate-200 pl-4 dark:border-slate-800">
                  {group.items.map((entry) => (
                    <div
                      key={entry.id}
                      className="flex items-start justify-between gap-3 text-sm"
                      data-who={entry.source === "ai" ? "ia" : entry.actor_user_id || ""}
                      data-kind={entry.entity_type || ""}
                    >
                      <div className="flex items-start gap-3 min-w-0 flex-1">
                        {entry.source === "ai" ? (
                          <Avatar kind="ai" name="Asistente CASE" size="sm" />
                        ) : (
                          <Avatar
                            kind="user"
                            name={entry.actor_display_name || "Usuario"}
                            userId={entry.actor_user_id || undefined}
                            size="sm"
                          />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="text-slate-800 dark:text-slate-200">
                            <b>
                              {entry.source === "ai"
                                ? "La IA aplicó:"
                                : entry.actor_display_name || "Usuario"}
                            </b>{" "}
                            {entry.summary}
                          </p>
                          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                            {getEntryBadge(entry)}
                            {entry.metadata && typeof entry.metadata === "object" && (
                              <>
                                {entry.metadata.confirmed_by && (
                                  <span>confirmado por {String(entry.metadata.confirmed_by)}</span>
                                )}
                                {entry.metadata.diagram_name && (
                                  <span>· {String(entry.metadata.diagram_name)}</span>
                                )}
                                {entry.metadata.file_name && (
                                  <span>{String(entry.metadata.file_name)}</span>
                                )}
                                {entry.metadata.file_count && (
                                  <span>· {String(entry.metadata.file_count)} archivos</span>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                      <time
                        className="shrink-0 text-xs text-slate-500 dark:text-slate-400"
                        dateTime={entry.occurred_at}
                      >
                        {formatRelativeTime(entry.occurred_at)}
                      </time>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer info & pagination */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
          {nextCursor ? (
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-md border border-slate-300 bg-white px-4 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              disabled={loadingMore}
              onClick={() => void handleLoadMore()}
            >
              {loadingMore ? <LoaderCircle className="mr-2 animate-spin" size={14} /> : null}
              Cargar más
            </button>
          ) : (
            <span className="text-xs text-slate-400">Fin del registro</span>
          )}
          <span className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <Database size={14} />
            {source === "postgres_fallback" ? (
              <span>Mostrando auditoría de PostgreSQL</span>
            ) : (
              <span>
                Guardado en Redis Streams ·{" "}
                <code className="rounded bg-slate-100 px-1 py-0.5 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                  case:changelog:project:{projectId.slice(0, 8)}…
                </code>
              </span>
            )}
          </span>
        </div>
      </div>
    </div>
  );
}
