import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { servicioNotificacionesPush } from "../../core/notifications/servicioNotificacionesPush";
import { BotonNotificacionesPush } from "./BotonNotificacionesPush";

vi.mock("../../core/notifications/servicioNotificacionesPush", () => ({
  servicioNotificacionesPush: {
    state: vi.fn(),
    subscribe: vi.fn(),
    unsubscribe: vi.fn(),
    sendTest: vi.fn()
  }
}));

describe("PushNotificationButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("activa la suscripcion y solicita una notificacion de prueba", async () => {
    vi.mocked(servicioNotificacionesPush.state).mockResolvedValue("available");
    vi.mocked(servicioNotificacionesPush.subscribe).mockResolvedValue();
    vi.mocked(servicioNotificacionesPush.sendTest).mockResolvedValue();

    render(<BotonNotificacionesPush />);
    const button = await screen.findByRole("button", { name: "Activar notificaciones" });
    fireEvent.click(button);

    await waitFor(() => expect(servicioNotificacionesPush.subscribe).toHaveBeenCalledOnce());
    expect(servicioNotificacionesPush.sendTest).toHaveBeenCalledOnce();
    expect(await screen.findByRole("button", { name: "Desactivar notificaciones" })).toBeEnabled();
  });

  it("elimina una suscripcion activa", async () => {
    vi.mocked(servicioNotificacionesPush.state).mockResolvedValue("subscribed");
    vi.mocked(servicioNotificacionesPush.unsubscribe).mockResolvedValue();

    render(<BotonNotificacionesPush />);
    const button = await screen.findByRole("button", { name: "Desactivar notificaciones" });
    fireEvent.click(button);

    await waitFor(() => expect(servicioNotificacionesPush.unsubscribe).toHaveBeenCalledOnce());
    expect(await screen.findByRole("button", { name: "Activar notificaciones" })).toBeEnabled();
  });
});
