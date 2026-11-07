import { useState } from "react";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { temaPredeterminadoV2 } from "../theme/contratoTema";
import { EspacioEstilosFlutter } from "./EspacioEstilosFlutter";

const mocks = vi.hoisted(() => ({
  obtenerTema: vi.fn(), listarPreajustes: vi.fn(), manifiestoInterfaz: vi.fn(), guardarTema: vi.fn(),
}));

vi.mock("../../../core/websocket/socketProyecto", () => ({
  ClienteSocketProyecto: class { conectar() {} cerrar() {} }
}));
vi.mock("../services/servicioGeneracion", () => ({ servicioGeneracion: {
  ...mocks, crearPreajuste: vi.fn(), eliminarPreajuste: vi.fn()
} }));

afterEach(() => cleanup());

describe("FlutterStyleWorkspace", () => {
  it("refleja opciones visuales y navega entre módulos y pantallas", async () => {
    mocks.obtenerTema.mockResolvedValue({ theme: temaPredeterminadoV2, revision: 1, diagnostics: [], valid: true });
    mocks.listarPreajustes.mockResolvedValue([]);
    mocks.manifiestoInterfaz.mockResolvedValue({
      schema_version: 1, source_hash: "hash", source_transformation_id: "tx", supported_states: ["content", "error"], diagnostics: [],
      modules: [
        { id: "venta", name: "venta", label: "Venta", icon: "folder", screens: [
          { id: "venta-list", kind: "list", title: "Ventas", fields: [], actions: [{ id: "confirmar", label: "Confirmar venta", interaction: "form", placement: "list", confirmation_required: true, icon: "check" }] },
          { id: "venta-form", kind: "form", title: "Formulario venta", fields: [{ id: "nombre", name: "nombre", label: "Nombre", control: "text_input", required: true, logical_type: "string" }], actions: [] },
        ] },
        { id: "curso", name: "curso", label: "Curso", icon: "folder", screens: [{ id: "curso-list", kind: "list", title: "Cursos", fields: [], actions: [] }] },
      ],
    });
    function ControlledWorkspace() {
      const [value, setValue] = useState(temaPredeterminadoV2);
      return <EspacioEstilosFlutter projectId="project" transformationId="tx" value={value} onChange={setValue} />;
    }
    render(<ControlledWorkspace />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Confirmar venta" })).toBeInTheDocument());
    const preview = screen.getByTestId("flutter-preview");
    fireEvent.change(screen.getByLabelText("Modo predeterminado"), { target: { value: "dark" } });
    expect(preview).toHaveStyle({ background: temaPredeterminadoV2.dark.background });
    fireEvent.change(screen.getByLabelText("Escala tipografica"), { target: { value: "large" } });
    expect(preview).toHaveStyle({ fontSize: "1.2em" });
    fireEvent.change(screen.getByLabelText("Peso base"), { target: { value: "medium" } });
    expect(preview).toHaveStyle({ fontWeight: "500" });
    fireEvent.change(screen.getByLabelText("Viewport"), { target: { value: "tablet" } });
    expect(preview).toHaveAttribute("data-viewport", "tablet");
    fireEvent.click(screen.getByRole("button", { name: "Confirmar venta" }));
    expect(screen.getByRole("dialog", { name: "Diálogo de ejemplo" })).toBeVisible();
    fireEvent.click(within(screen.getByRole("dialog", { name: "Diálogo de ejemplo" })).getByRole("button", { name: "Cancelar" }));
    fireEvent.change(screen.getByLabelText(/dialog radius/), { target: { value: "20" } });
    expect(screen.getByRole("dialog", { name: "Diálogo de ejemplo" })).toHaveStyle({ borderRadius: "20px" });
    fireEvent.click(screen.getByRole("button", { name: "Cerrar diálogo" }));
    fireEvent.change(screen.getByLabelText("Pantalla"), { target: { value: "venta-form" } });
    expect(screen.getByRole("heading", { name: "Formulario venta" })).toBeVisible();
    fireEvent.change(screen.getByLabelText("Card"), { target: { value: "elevated" } });
    expect(screen.getByLabelText("Pantalla")).toHaveValue("venta-list");
    fireEvent.change(screen.getByLabelText("Campo"), { target: { value: "filled" } });
    expect(screen.getByLabelText("Pantalla")).toHaveValue("venta-form");
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "error" } });
    expect(screen.getByRole("status")).toHaveTextContent("No se pudo cargar");
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "content" } });
    const nav = screen.getByRole("navigation", { name: "Navegacion inferior del preview" });
    fireEvent.click(within(nav).getByRole("button", { name: "Curso" }));
    expect(screen.getByLabelText("Modulo")).toHaveValue("curso");
    expect(screen.getByLabelText("Pantalla")).toHaveValue("curso-list");
  });
  it("carga tema y representa entidades reales del ui_manifest", async () => {
    mocks.obtenerTema.mockResolvedValue({ theme: temaPredeterminadoV2, revision: 3, diagnostics: [], valid: true });
    mocks.listarPreajustes.mockResolvedValue([]);
    mocks.manifiestoInterfaz.mockResolvedValue({ schema_version: 1, source_hash: "abc123456789", source_transformation_id: "tx", supported_states: ["content"], diagnostics: [], modules: [{ id: "curso", name: "curso", label: "Curso", icon: "folder", screens: [{ id: "curso-list", kind: "list", title: "Curso", fields: [{ id: "nombre", name: "nombre", label: "Nombre", control: "text_input", required: true, logical_type: "string" }], actions: [] }] }] });
    const onChange = vi.fn();
    render(<EspacioEstilosFlutter projectId="project" transformationId="tx" value={temaPredeterminadoV2} onChange={onChange} />);
    await waitFor(() => expect(screen.getAllByText("Curso").length).toBeGreaterThan(0));
    expect(screen.getAllByText("nombre de ejemplo", { exact: false })).toHaveLength(3);
    expect(screen.getByText("Revision 3 · Guardado")).toBeInTheDocument();
  });

  it("aplica un cambio al borrador sin guardarlo automaticamente", async () => {
    mocks.obtenerTema.mockResolvedValue({ theme: temaPredeterminadoV2, revision: 1, diagnostics: [], valid: true });
    mocks.listarPreajustes.mockResolvedValue([]);
    mocks.manifiestoInterfaz.mockResolvedValue({ schema_version: 1, source_hash: "hash", source_transformation_id: "tx", supported_states: [], diagnostics: [], modules: [] });
    const onChange = vi.fn();
    render(<EspacioEstilosFlutter projectId="project" transformationId="tx" value={temaPredeterminadoV2} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("Selector primary"), { target: { value: "#123456" } });
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ light: expect.objectContaining({ primary: "#123456" }) }));
    expect(mocks.guardarTema).not.toHaveBeenCalled();
  });
});
