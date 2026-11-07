import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { servicioNotificacionesPush } from "../../core/notifications/servicioNotificacionesPush";
import { BotonNotificacionesPush } from "./BotonNotificacionesPush";

vi.mock("../../core/notifications/servicioNotificacionesPush", () => ({
  servicioNotificacionesPush: {
    estado: vi.fn(),
    suscribir: vi.fn(),
    cancelarSuscripcion: vi.fn(),
    enviarPrueba: vi.fn()
  }
}));

describe("PushNotificationButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("activa la suscripcion y solicita una notificacion de prueba", async () => {
    vi.mocked(servicioNotificacionesPush.estado).mockResolvedValue("available");
    vi.mocked(servicioNotificacionesPush.suscribir).mockResolvedValue();
    vi.mocked(servicioNotificacionesPush.enviarPrueba).mockResolvedValue();

    render(<BotonNotificacionesPush />);
    const button = await screen.findByRole("button", { name: "Activar notificaciones" });
    fireEvent.click(button);

    await waitFor(() => expect(servicioNotificacionesPush.suscribir).toHaveBeenCalledOnce());
    expect(servicioNotificacionesPush.enviarPrueba).toHaveBeenCalledOnce();
    expect(await screen.findByRole("button", { name: "Desactivar notificaciones" })).toBeEnabled();
  });

  it("elimina una suscripcion activa", async () => {
    vi.mocked(servicioNotificacionesPush.estado).mockResolvedValue("subscribed");
    vi.mocked(servicioNotificacionesPush.cancelarSuscripcion).mockResolvedValue();

    render(<BotonNotificacionesPush />);
    const button = await screen.findByRole("button", { name: "Desactivar notificaciones" });
    fireEvent.click(button);

    await waitFor(() => expect(servicioNotificacionesPush.cancelarSuscripcion).toHaveBeenCalledOnce());
    expect(await screen.findByRole("button", { name: "Activar notificaciones" })).toBeEnabled();
  });
});
