import { beforeEach, describe, expect, it, vi } from "vitest";

import { clienteApi } from "../../../core/api/cliente";
import { servicio_ia } from "./servicio_ia";

vi.mock("../../../core/api/cliente", () => ({
  clienteApi: { post: vi.fn(), get: vi.fn() }
}));

const clienteSimulado = vi.mocked(clienteApi);

describe("servicio_ia: entradas al modelo UML", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clienteSimulado.post.mockResolvedValue({ data: { classes: [], relationships: [] } });
  });

  it("envía texto por la ruta de texto", async () => {
    await servicio_ia.textoAUml("Sistema de ventas");
    expect(clienteSimulado.post).toHaveBeenCalledWith("/ai/uml/text", {
      prompt: "Sistema de ventas", language: "es", source_type: "text"
    });
  });

  it("envía la transcripción por la ruta de voz", async () => {
    await servicio_ia.vozAUml({ transcript: "Crear una clase" });
    expect(clienteSimulado.post).toHaveBeenCalledWith("/ai/uml/voice", {
      transcript: "Crear una clase", language: "es"
    });
  });

  it("envía imagen y metadatos por la ruta de imagen", async () => {
    await servicio_ia.imagenAUml({ image_base64: "abc", file_name: "diagrama.jpeg" });
    expect(clienteSimulado.post).toHaveBeenCalledWith("/ai/uml/image", {
      image_base64: "abc", file_name: "diagrama.jpeg", language: "es"
    });
  });
});
