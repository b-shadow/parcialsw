/* global self, URL */

self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = { body: event.data ? event.data.text() : "Tienes una nueva notificacion." };
  }
  const title = payload.title || "CASE Inteligente";
  const options = {
    body: payload.body || "Hay novedades en tu espacio de trabajo.",
    icon: "/pwa-icon.svg",
    badge: "/pwa-icon.svg",
    tag: payload.tag || "case-notification",
    renotify: false,
    data: { url: payload.url || "/", ...(payload.data || {}) }
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
