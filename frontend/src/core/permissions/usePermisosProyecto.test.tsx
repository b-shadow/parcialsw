import { act, cleanup, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clienteApi } from "../api/cliente";
import { ControlPermisos } from "./ControlPermisos";
import { useAlmacenPermisos, usePermisosProyecto } from "./usePermisosProyecto";

vi.mock("../api/cliente", () => ({
  clienteApi: {
    get: vi.fn(),
  },
}));

describe("useProjectPermissions & PermissionGate", () => {
  beforeEach(() => {
    useAlmacenPermisos.getState().invalidate();
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("mientras carga -> can() devuelve false", () => {
    let resolvePromise: (value: unknown) => void = () => {};
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(clienteApi.get).mockReturnValueOnce(pendingPromise as unknown as ReturnType<typeof clienteApi.get>);

    const { result } = renderHook(() => usePermisosProyecto("proj-1"));

    expect(result.current.loading).toBe(true);
    expect(result.current.can("uml.edit")).toBe(false);
    expect(result.current.can("project.read")).toBe(false);

    // Resolve promise to clean up
    act(() => {
      resolvePromise({
        data: {
          project_id: "proj-1",
          user_id: "user-1",
          project_role: "EDITOR",
          permissions: ["uml.edit"],
        },
      });
    });
  });

  it("respuesta EDITOR -> can('uml.edit') true y can('members.manage') false", async () => {
    vi.mocked(clienteApi.get).mockResolvedValueOnce({
      data: {
        project_id: "proj-editor",
        user_id: "user-editor",
        project_role: "EDITOR",
        permissions: ["project.read", "uml.edit", "ai.chat", "generation.run", "theme.edit"],
      },
    });

    const { result } = renderHook(() => usePermisosProyecto("proj-editor"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.role).toBe("EDITOR");
    expect(result.current.can("uml.edit")).toBe(true);
    expect(result.current.can("members.manage")).toBe(false);
    expect(result.current.can("project.update")).toBe(false);
  });

  it("dos componentes con el mismo projectId -> una sola petición", async () => {
    let resolvePromise: (value: unknown) => void = () => {};
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(clienteApi.get).mockReturnValue(pendingPromise as unknown as ReturnType<typeof clienteApi.get>);

    const { result: r1 } = renderHook(() => usePermisosProyecto("proj-shared"));
    const { result: r2 } = renderHook(() => usePermisosProyecto("proj-shared"));

    expect(clienteApi.get).toHaveBeenCalledTimes(1);
    expect(clienteApi.get).toHaveBeenCalledWith("/projects/proj-shared/members/me");

    await act(async () => {
      resolvePromise({
        data: {
          project_id: "proj-shared",
          user_id: "user-1",
          project_role: "ORGANIZADOR",
          permissions: ["project.read", "uml.edit", "members.manage"],
        },
      });
    });

    await waitFor(() => {
      expect(r1.current.loading).toBe(false);
      expect(r2.current.loading).toBe(false);
    });

    expect(r1.current.can("members.manage")).toBe(true);
    expect(r2.current.can("members.manage")).toBe(true);
    expect(clienteApi.get).toHaveBeenCalledTimes(1);
  });

  it("PermissionGate oculta children sin el permiso y muestra fallback", async () => {
    vi.mocked(clienteApi.get).mockResolvedValue({
      data: {
        project_id: "proj-gate",
        user_id: "user-gate",
        project_role: "LECTOR",
        permissions: ["project.read"],
      },
    });

    const { rerender } = render(
      <ControlPermisos
        projectId="proj-gate"
        code="uml.edit"
        fallback={<span data-testid="fallback">Sin permiso</span>}
      >
        <button data-testid="action-btn">Editar UML</button>
      </ControlPermisos>
    );

    // Initial render / while loading fallback
    expect(screen.queryByTestId("action-btn")).toBeNull();

    await waitFor(() => {
      expect(screen.getByTestId("fallback")).toBeTruthy();
    });
    expect(screen.queryByTestId("action-btn")).toBeNull();

    // Now test with permission granted
    useAlmacenPermisos.getState().invalidate();
    vi.mocked(clienteApi.get).mockResolvedValue({
      data: {
        project_id: "proj-gate-2",
        user_id: "user-gate-2",
        project_role: "EDITOR",
        permissions: ["project.read", "uml.edit"],
      },
    });

    rerender(
      <ControlPermisos
        projectId="proj-gate-2"
        code="uml.edit"
        fallback={<span data-testid="fallback">Sin permiso</span>}
      >
        <button data-testid="action-btn">Editar UML</button>
      </ControlPermisos>
    );

    await waitFor(() => {
      expect(screen.getByTestId("action-btn")).toBeTruthy();
    });
    expect(screen.queryByTestId("fallback")).toBeNull();
  });
});
