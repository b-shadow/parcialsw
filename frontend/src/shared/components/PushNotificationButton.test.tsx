import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { pushNotificationService } from "../../core/notifications/pushNotificationService";
import { PushNotificationButton } from "./PushNotificationButton";

vi.mock("../../core/notifications/pushNotificationService", () => ({
  pushNotificationService: {
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
    vi.mocked(pushNotificationService.state).mockResolvedValue("available");
    vi.mocked(pushNotificationService.subscribe).mockResolvedValue();
    vi.mocked(pushNotificationService.sendTest).mockResolvedValue();

    render(<PushNotificationButton />);
    const button = await screen.findByRole("button", { name: "Activar notificaciones" });
    fireEvent.click(button);

    await waitFor(() => expect(pushNotificationService.subscribe).toHaveBeenCalledOnce());
    expect(pushNotificationService.sendTest).toHaveBeenCalledOnce();
    expect(await screen.findByRole("button", { name: "Desactivar notificaciones" })).toBeEnabled();
  });

  it("elimina una suscripcion activa", async () => {
    vi.mocked(pushNotificationService.state).mockResolvedValue("subscribed");
    vi.mocked(pushNotificationService.unsubscribe).mockResolvedValue();

    render(<PushNotificationButton />);
    const button = await screen.findByRole("button", { name: "Desactivar notificaciones" });
    fireEvent.click(button);

    await waitFor(() => expect(pushNotificationService.unsubscribe).toHaveBeenCalledOnce());
    expect(await screen.findByRole("button", { name: "Activar notificaciones" })).toBeEnabled();
  });
});
