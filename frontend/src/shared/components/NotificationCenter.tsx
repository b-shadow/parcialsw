import { useCallback, useEffect, useRef, useState } from "react";
import { Bell, CheckCheck, CircleAlert, Inbox, LoaderCircle, X } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

import {
  notificationPath,
  notificationService,
  type InboxNotification
} from "../../core/notifications/notificationService";
import { cn } from "../utils/cn";

function moment(value: string) {
  return new Intl.DateTimeFormat("es", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit"
  }).format(new Date(value));
}

export function NotificationCenter() {
  const navigate = useNavigate();
  const location = useLocation();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<InboxNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (append = false, requestedCursor?: string | null) => {
    setLoading(true);
    setError("");
    try {
      const [page, count] = await Promise.all([
        notificationService.list(append ? requestedCursor ?? undefined : undefined),
        notificationService.unreadCount()
      ]);
      setItems((current) => append ? [...current, ...page.items] : page.items);
      setCursor(page.next_cursor);
      setHasMore(page.has_more);
      setUnread(count);
    } catch {
      setError("No se pudieron cargar las notificaciones.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void notificationService.unreadCount().then(setUnread).catch(() => undefined);
    const timer = window.setInterval(() => {
      void notificationService.unreadCount().then(setUnread).catch(() => undefined);
    }, 30_000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const query = new URLSearchParams(location.search);
    const notificationId = query.get("notification_id");
    if (!notificationId) return;
    void notificationService.clicked(notificationId).then(() => {
      query.delete("notification_id");
      navigate(`${location.pathname}${query.toString() ? `?${query}` : ""}`, { replace: true });
    }).catch(() => undefined);
  }, [location.pathname, location.search, navigate]);

  useEffect(() => {
    const refresh = (raw: Event) => {
      const detail = (raw as CustomEvent<Record<string, unknown>>).detail;
      if (["NOTIFICATION_CREATED", "PROJECT_VERSION_CREATED", "PROJECT_VERSION_RESTORED"].includes(String(detail?.type))) {
        void notificationService.unreadCount().then(setUnread).catch(() => undefined);
        if (open) void load(false);
      }
    };
    window.addEventListener("case:project-socket-event", refresh);
    return () => window.removeEventListener("case:project-socket-event", refresh);
  }, [load, open]);

  useEffect(() => {
    if (open) void load(false);
  }, [load, open]);

  async function select(item: InboxNotification) {
    const updated = await notificationService.clicked(item.id);
    setItems((current) => current.map((value) => value.id === item.id ? updated : value));
    setUnread((value) => Math.max(0, value - (item.read_at ? 0 : 1)));
    setOpen(false);
    navigate(notificationPath(item.deep_link));
    buttonRef.current?.focus();
  }

  async function readAll() {
    await notificationService.markAllRead();
    setItems((current) => current.map((item) => ({ ...item, read_at: item.read_at ?? new Date().toISOString() })));
    setUnread(0);
  }

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        aria-label={`Notificaciones${unread ? `, ${unread} sin leer` : ""}`}
        aria-expanded={open}
        className="relative flex h-10 w-10 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
        onClick={() => setOpen((value) => !value)} title="Notificaciones" type="button"
      >
        <Bell size={20} aria-hidden="true" />
        {unread > 0 ? <span className="absolute -right-1 -top-1 min-w-5 rounded-full bg-red-600 px-1 text-center text-[10px] font-bold leading-5 text-white">{unread > 99 ? "99+" : unread}</span> : null}
      </button>
      {open ? (
        <section aria-label="Bandeja de notificaciones" className="fixed inset-x-3 top-20 z-50 flex max-h-[calc(100vh-6rem)] flex-col overflow-hidden rounded-md border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-950 sm:absolute sm:inset-x-auto sm:right-0 sm:top-12 sm:w-[390px]">
          <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
            <div><h2 className="text-sm font-bold">Notificaciones</h2><p className="text-xs text-slate-500">{unread ? `${unread} sin leer` : "Todo al dia"}</p></div>
            <div className="flex gap-1">
              <button aria-label="Marcar todas como leidas" className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => void readAll()} title="Marcar todas como leidas" type="button"><CheckCheck size={18} /></button>
              <button aria-label="Cerrar notificaciones" className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => setOpen(false)} title="Cerrar" type="button"><X size={18} /></button>
            </div>
          </header>
          <div className="overflow-y-auto">
            {items.map((item) => (
              <button key={item.id} className={cn("flex w-full gap-3 border-b border-slate-100 px-4 py-3 text-left dark:border-slate-800", !item.read_at && "bg-teal-50/70 dark:bg-teal-950/20")} onClick={() => void select(item)} type="button">
                <span className="mt-0.5 text-teal-700">{item.severity === "error" ? <CircleAlert size={18} /> : <Inbox size={18} />}</span>
                <span className="min-w-0 flex-1"><span className="block text-sm font-bold">{item.title}</span><span className="mt-1 block text-xs leading-5 text-slate-600 dark:text-slate-300">{item.body}</span><time className="mt-1 block text-[11px] text-slate-400">{moment(item.occurred_at)}</time></span>
              </button>
            ))}
            {!items.length && !loading && !error ? <p className="px-4 py-10 text-center text-sm text-slate-500">No tienes notificaciones.</p> : null}
            {error ? <button className="w-full px-4 py-6 text-sm text-red-600" onClick={() => void load(false)} type="button">{error} Reintentar</button> : null}
            {loading ? <p className="flex items-center justify-center gap-2 px-4 py-5 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={17} /> Cargando</p> : null}
            {hasMore && !loading ? <button className="w-full px-4 py-3 text-sm font-bold text-teal-700" onClick={() => void load(true, cursor)} type="button">Cargar anteriores</button> : null}
          </div>
        </section>
      ) : null}
    </div>
  );
}
