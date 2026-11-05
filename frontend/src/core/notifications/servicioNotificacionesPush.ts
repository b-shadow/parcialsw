import { clienteApi } from "../api/cliente";

type PushConfig = {
  enabled: boolean;
  public_key: string | null;
};

export type EstadoNotificacionPush = "unsupported" | "disabled" | "available" | "subscribed";

function urlBase64ToUint8Array(value: string) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  return Uint8Array.from([...raw].map((character) => character.charCodeAt(0)));
}

function isSupported() {
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

export const servicioNotificacionesPush = {
  async state(): Promise<EstadoNotificacionPush> {
    if (!isSupported()) {
      return "unsupported";
    }
    const { data: config } = await clienteApi.get<PushConfig>("/notifications/push/config");
    if (!config.enabled || !config.public_key) {
      return "disabled";
    }
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    return subscription ? "subscribed" : "available";
  },

  async subscribe(): Promise<void> {
    if (!isSupported()) {
      throw new Error("Este navegador no admite notificaciones push.");
    }
    const { data: config } = await clienteApi.get<PushConfig>("/notifications/push/config");
    if (!config.enabled || !config.public_key) {
      throw new Error("Las notificaciones push todavia no estan configuradas en el servidor.");
    }
    const permission = await Notification.requestPermission();
    if (permission !== "granted") {
      throw new Error("El navegador no concedio permiso para mostrar notificaciones.");
    }
    const registration = await navigator.serviceWorker.ready;
    const existing = await registration.pushManager.getSubscription();
    const subscription = existing ?? await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(config.public_key)
    });
    const serialized = subscription.toJSON();
    if (!serialized.endpoint || !serialized.keys?.p256dh || !serialized.keys.auth) {
      throw new Error("El navegador devolvio una suscripcion incompleta.");
    }
    await clienteApi.post("/notifications/push/subscriptions", {
      endpoint: serialized.endpoint,
      expiration_time: serialized.expirationTime
        ? new Date(serialized.expirationTime).toISOString()
        : null,
      keys: serialized.keys
    });
  },

  async unsubscribe(): Promise<void> {
    if (!isSupported()) {
      return;
    }
    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      return;
    }
    await clienteApi.delete("/notifications/push/subscriptions", {
      data: { endpoint: subscription.endpoint }
    });
    await subscription.unsubscribe();
  },

  async sendTest(): Promise<void> {
    await clienteApi.post("/notifications/push/test");
  }
};
