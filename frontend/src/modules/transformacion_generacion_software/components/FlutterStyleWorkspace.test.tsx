import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { defaultThemeV2 } from "../theme/themeContract";
import { FlutterStyleWorkspace } from "./FlutterStyleWorkspace";

const mocks = vi.hoisted(() => ({
  getTheme: vi.fn(), presets: vi.fn(), uiManifest: vi.fn(), saveTheme: vi.fn(),
}));

vi.mock("../../../core/websocket/projectSocket", () => ({
  ProjectSocketClient: class { connect() {} close() {} }
}));
vi.mock("../services/generationService", () => ({ generationService: {
  ...mocks, createPreset: vi.fn(), deletePreset: vi.fn()
} }));

afterEach(() => cleanup());

describe("FlutterStyleWorkspace", () => {
  it("carga tema y representa entidades reales del ui_manifest", async () => {
    mocks.getTheme.mockResolvedValue({ theme: defaultThemeV2, revision: 3, diagnostics: [], valid: true });
    mocks.presets.mockResolvedValue([]);
    mocks.uiManifest.mockResolvedValue({ schema_version: 1, source_hash: "abc123456789", source_transformation_id: "tx", supported_states: ["content"], diagnostics: [], modules: [{ id: "curso", name: "curso", label: "Curso", icon: "folder", screens: [{ id: "curso-list", kind: "list", title: "Curso", fields: [{ id: "nombre", name: "nombre", label: "Nombre", control: "text_input", required: true, logical_type: "string" }], actions: [] }] }] });
    const onChange = vi.fn();
    render(<FlutterStyleWorkspace projectId="project" transformationId="tx" value={defaultThemeV2} onChange={onChange} />);
    await waitFor(() => expect(screen.getAllByText("Curso").length).toBeGreaterThan(0));
    expect(screen.getAllByText("nombre de ejemplo", { exact: false })).toHaveLength(3);
    expect(screen.getByText("Revision 3 · Guardado")).toBeInTheDocument();
  });

  it("aplica un cambio al borrador sin guardarlo automaticamente", async () => {
    mocks.getTheme.mockResolvedValue({ theme: defaultThemeV2, revision: 1, diagnostics: [], valid: true });
    mocks.presets.mockResolvedValue([]);
    mocks.uiManifest.mockResolvedValue({ schema_version: 1, source_hash: "hash", source_transformation_id: "tx", supported_states: [], diagnostics: [], modules: [] });
    const onChange = vi.fn();
    render(<FlutterStyleWorkspace projectId="project" transformationId="tx" value={defaultThemeV2} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Selector primary"), { target: { value: "#123456" } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ light: expect.objectContaining({ primary: "#123456" }) }));
    expect(mocks.saveTheme).not.toHaveBeenCalled();
  });
});
