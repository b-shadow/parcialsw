import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ChangeLogEntry, ChangeLogPage } from "../../../core/contracts/mejoras2p";
import type { ParsedProjectSocketEvent } from "../../../core/websocket/projectSocket";
import { ChangeLogPanel } from "./ChangeLogPanel";

type CapturedSocketOptions = {
  onEvent: (event: ParsedProjectSocketEvent | Record<string, unknown>) => void;
};

let capturedSocketOptions: CapturedSocketOptions | null = null;

vi.mock("../../../core/websocket/projectSocket", () => ({
  ProjectSocketClient: class {
    constructor(options: CapturedSocketOptions) {
      capturedSocketOptions = options;
    }
    connect() {}
    close() {}
  },
}));

const mockList = vi.fn();
vi.mock("../services/changeLogService", () => ({
  changeLogService: {
    list: (projectId: string, params?: unknown) => mockList(projectId, params),
  },
}));

vi.mock("../services/projectService", () => ({
  projectService: {
    members: vi.fn().mockResolvedValue([
      { id: "m-1", user_id: "user-1", full_name: "Ana Dev", email: "ana@example.com" },
      { id: "m-2", user_id: "user-2", full_name: "Beto Dev", email: "beto@example.com" },
    ]),
  },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  capturedSocketOptions = null;
});

const sampleEntry1: ChangeLogEntry = {
  id: "entry-1",
  project_id: "p-100",
  occurred_at: new Date(Date.now() - 120_000).toISOString(), // 2 mins ago
  actor_user_id: "user-1",
  actor_display_name: "Ana Dev",
  source: "ui",
  module: "modelado_uml",
  action: "CREATE_CLASS",
  entity_type: "class",
  entity_id: "c-1",
  diagram_id: "d-1",
  summary: "creó la clase Factura",
  metadata: { confirmed_by: "Ana Dev" },
};

const sampleEntry2: ChangeLogEntry = {
  id: "entry-2",
  project_id: "p-100",
  occurred_at: new Date(Date.now() - 3600_000).toISOString(), // 1 hour ago
  actor_user_id: null,
  actor_display_name: "Asistente CASE",
  source: "ai",
  module: "asistente_proyecto",
  action: "AI_ACTION_APPLIED",
  entity_type: "ai_action",
  entity_id: null,
  diagram_id: null,
  summary: "aplicó 3 recomendaciones",
  metadata: {},
};

describe("ChangeLogPanel", () => {
  it("renderiza autor, resumen y hora relativa de cada entrada", async () => {
    const page: ChangeLogPage = {
      items: [sampleEntry1, sampleEntry2],
      next_cursor: null,
      source: "redis",
    };
    mockList.mockResolvedValueOnce(page);

    render(<ChangeLogPanel projectId="p-100" />);

    await waitFor(() => {
      expect(screen.getAllByText("Ana Dev").length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.getByText(/creó la clase Factura/)).toBeInTheDocument();
    expect(screen.getByText("La IA aplicó:")).toBeInTheDocument();
    expect(screen.getByText(/aplicó 3 recomendaciones/)).toBeInTheDocument();
    expect(screen.getAllByText(/hace /).length).toBeGreaterThan(0);
  });

  it("muestra banner «Registro en modo respaldo» cuando source='postgres_fallback'", async () => {
    const page: ChangeLogPage = {
      items: [sampleEntry1],
      next_cursor: null,
      source: "postgres_fallback",
    };
    mockList.mockResolvedValueOnce(page);

    render(<ChangeLogPanel projectId="p-100" />);

    await waitFor(() => {
      expect(
        screen.getByText(/Registro en modo respaldo: Redis no responde/i)
      ).toBeInTheDocument();
    });
  });

  it("agrega evento CHANGE_LOGGED con id nuevo arriba y no duplica con id repetido", async () => {
    const page: ChangeLogPage = {
      items: [sampleEntry1],
      next_cursor: null,
      source: "redis",
    };
    mockList.mockResolvedValueOnce(page);

    render(<ChangeLogPanel projectId="p-100" />);

    await waitFor(() => {
      expect(screen.getByText(/creó la clase Factura/)).toBeInTheDocument();
    });

    // Simulate incoming new CHANGE_LOGGED event
    const newEntry: ChangeLogEntry = {
      id: "entry-live-new",
      project_id: "p-100",
      occurred_at: new Date().toISOString(),
      actor_user_id: "user-2",
      actor_display_name: "Beto Dev",
      source: "ui",
      module: "modelado_uml",
      action: "CREATE_CLASS",
      entity_type: "class",
      entity_id: "c-2",
      diagram_id: null,
      summary: "creó la clase Producto",
      metadata: {},
    };

    act(() => {
      capturedSocketOptions?.onEvent({
        type: "CHANGE_LOGGED",
        payload: { entry: newEntry },
      });
    });

    expect(screen.getByText(/creó la clase Producto/)).toBeInTheDocument();

    // Re-dispatching same ID should not duplicate it
    act(() => {
      capturedSocketOptions?.onEvent({
        type: "CHANGE_LOGGED",
        payload: { entry: newEntry },
      });
    });

    const matches = screen.getAllByText(/creó la clase Producto/);
    expect(matches).toHaveLength(1);
  });

  it("filtro por integrante llama al servicio con actor_id", async () => {
    const page: ChangeLogPage = {
      items: [sampleEntry1],
      next_cursor: null,
      source: "redis",
    };
    mockList.mockResolvedValue(page);

    render(<ChangeLogPanel projectId="p-100" />);

    await waitFor(() => {
      expect(screen.getByLabelText("Integrante")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Integrante"), {
      target: { value: "user-1" },
    });

    await waitFor(() => {
      expect(mockList).toHaveBeenCalledWith(
        "p-100",
        expect.objectContaining({ actor_id: "user-1" })
      );
    });
  });

  it("«Cargar más» usa next_cursor como before_id", async () => {
    const firstPage: ChangeLogPage = {
      items: [sampleEntry1],
      next_cursor: "1729432000000-0",
      source: "redis",
    };
    const secondPage: ChangeLogPage = {
      items: [sampleEntry2],
      next_cursor: null,
      source: "redis",
    };
    mockList.mockResolvedValueOnce(firstPage).mockResolvedValueOnce(secondPage);

    render(<ChangeLogPanel projectId="p-100" />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Cargar más/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Cargar más/i }));

    await waitFor(() => {
      expect(mockList).toHaveBeenCalledWith(
        "p-100",
        expect.objectContaining({ before_id: "1729432000000-0" })
      );
    });
  });
});
