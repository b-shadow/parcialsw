import { apiClient } from "../api/client";

export type NotificationDeepLink = {
  route_name: string;
  params?: Record<string, string>;
  query?: Record<string, string>;
};

export type InboxNotification = {
  id: string;
  project_id: string | null;
  actor_user_id: string | null;
  type: string;
  severity: "info" | "success" | "warning" | "error";
  title: string;
  body: string;
  deep_link: NotificationDeepLink;
  occurred_at: string;
  read_at: string | null;
  clicked_at: string | null;
};

export const notificationService = {
  async list(cursor?: string) {
    const response = await apiClient.get<{ items: InboxNotification[]; next_cursor: string | null; has_more: boolean }>("/notifications", { params: { cursor, limit: 30 } });
    return response.data;
  },
  async unreadCount() {
    const response = await apiClient.get<{ count: number }>("/notifications/unread-count");
    return response.data.count;
  },
  async markRead(id: string) {
    const response = await apiClient.post<InboxNotification>(`/notifications/${id}/read`);
    return response.data;
  },
  async clicked(id: string) {
    const response = await apiClient.post<InboxNotification>(`/notifications/${id}/clicked`);
    return response.data;
  },
  async markAllRead() {
    await apiClient.post("/notifications/read-all");
  }
};

export function notificationPath(link: NotificationDeepLink): string {
  const projectId = link.params?.project_id;
  const diagramId = link.params?.diagram_id;
  const routes: Record<string, string> = {
    projects: "/proyectos",
    project_management: projectId ? `/proyectos/${projectId}` : "/proyectos",
    project_collaborative: projectId ? `/proyectos/${projectId}/colaborativo` : "/proyectos",
    project_diagram: projectId && diagramId ? `/proyectos/${projectId}/uml/${diagramId}` : "/proyectos",
    project_ai: projectId ? `/proyectos/${projectId}/colaborativo` : "/proyectos",
    generation: "/generacion",
    profile: "/perfil"
  };
  const path = routes[link.route_name] ?? "/proyectos";
  const query = new URLSearchParams(link.query ?? {}).toString();
  return query ? `${path}?${query}` : path;
}
