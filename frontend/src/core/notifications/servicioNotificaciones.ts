import { clienteApi } from "../api/cliente";

export type EnlaceProfundoNotificacion = {
  route_name: string;
  params?: Record<string, string>;
  query?: Record<string, string>;
};

export type NotificacionBandeja = {
  id: string;
  project_id: string | null;
  actor_user_id: string | null;
  type: string;
  severity: "info" | "success" | "warning" | "error";
  title: string;
  body: string;
  deep_link: EnlaceProfundoNotificacion;
  occurred_at: string;
  read_at: string | null;
  clicked_at: string | null;
};

export const servicioNotificaciones = {
  async listar(cursor?: string) {
    const response = await clienteApi.get<{ items: NotificacionBandeja[]; next_cursor: string | null; has_more: boolean }>("/notifications", { params: { cursor, limit: 30 } });
    return response.data;
  },
  async cantidadNoLeidas() {
    const response = await clienteApi.get<{ count: number }>("/notifications/unread-count");
    return response.data.count;
  },
  async marcarLeida(id: string) {
    const response = await clienteApi.post<NotificacionBandeja>(`/notifications/${id}/read`);
    return response.data;
  },
  async abrir(id: string) {
    const response = await clienteApi.post<NotificacionBandeja>(`/notifications/${id}/clicked`);
    return response.data;
  },
  async marcarTodasLeidas() {
    await clienteApi.post("/notifications/read-all");
  }
};

export function rutaNotificacion(link: EnlaceProfundoNotificacion): string {
  const projectId = link.params?.project_id;
  const diagramId = link.params?.diagram_id;
  const rutas: Record<string, string> = {
    projects: "/proyectos",
    project_management: projectId ? `/proyectos/${projectId}` : "/proyectos",
    project_collaborative: projectId ? `/proyectos/${projectId}/colaborativo` : "/proyectos",
    project_diagram: projectId && diagramId ? `/proyectos/${projectId}/uml/${diagramId}` : "/proyectos",
    project_ai: projectId ? `/proyectos/${projectId}/colaborativo` : "/proyectos",
    generation: "/generacion",
    profile: "/perfil"
  };
  const path = rutas[link.route_name] ?? "/proyectos";
  const query = new URLSearchParams(link.query ?? {}).toString();
  return query ? `${path}?${query}` : path;
}
