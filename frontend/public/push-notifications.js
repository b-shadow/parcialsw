/* global self, URL, URLSearchParams */

self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = { body: event.data ? event.data.text() : "Tienes una nueva notificacion." };
  }
  const title = payload.title || "CASE Inteligente";
  const deepLink = payload.deep_link && typeof payload.deep_link === "object" ? payload.deep_link : null;
  const routes = {
    projects: "/proyectos",
    project_management: deepLink?.params?.project_id ? `/proyectos/${deepLink.params.project_id}` : "/proyectos",
    project_collaborative: deepLink?.params?.project_id ? `/proyectos/${deepLink.params.project_id}/colaborativo` : "/proyectos",
    project_diagram: deepLink?.params?.project_id && deepLink?.params?.diagram_id ? `/proyectos/${deepLink.params.project_id}/uml/${deepLink.params.diagram_id}` : "/proyectos",
    project_ai: deepLink?.params?.project_id ? `/proyectos/${deepLink.params.project_id}/colaborativo` : "/proyectos",
    generation: "/generacion",
    profile: "/perfil"
  };
  const basePath = deepLink ? routes[deepLink.route_name] || "/proyectos" : payload.url || "/";
  const query = new URLSearchParams(deepLink?.query || {});
  if (payload.notification_id) query.set("notification_id", payload.notification_id);
  const target = query.toString() ? `${basePath}?${query}` : basePath;
  const options = {
    body: payload.body || "Hay novedades en tu espacio de trabajo.",
    icon: "/pwa-icon.svg",
    badge: "/pwa-icon.svg",
    tag: payload.tag || "case-notification",
    renotify: false,
    data: { url: target, notification_id: payload.notification_id, ...(payload.data || {}) }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = new URL(event.notification.data?.url || "/", self.location.origin).href;
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      const existing = clients.find((client) => client.url.startsWith(self.location.origin));
      if (existing) {
        return existing.navigate(targetUrl).then((client) => client?.focus());
      }
      return self.clients.openWindow(targetUrl);
    })
  );
});
