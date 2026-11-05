import { describe, expect, it } from "vitest";

import { clienteApi } from "./cliente";
import { contratoAlCodigo, contratoAlEspanol } from "./contratoEspanol";

describe("contrato JSON en español", () => {
  it("traduce campos anidados y conserva los valores", () => {
    const anterior = { model_name: "qwen", classes: [{ name: "Curso" }] };
    const nuevo = { nombre_modelo: "qwen", clases: [{ nombre: "Curso" }] };
    expect(contratoAlEspanol(anterior)).toEqual(nuevo);
    expect(contratoAlCodigo(nuevo)).toEqual(anterior);
  });

  it("envía el contrato español por HTTP y entrega el modelo interno a la vista", async () => {
    const resultado = await clienteApi.post("/prueba", { model_name: "qwen" }, {
      adapter: async (config) => {
        expect(config.headers.get("X-Contrato-Idioma")).toBe("es");
        expect(JSON.parse(String(config.data))).toEqual({ nombre_modelo: "qwen" });
        return {
          config,
          data: { nombre_modelo: "qwen", clases: [{ nombre: "Curso" }] },
          headers: {},
          status: 200,
          statusText: "OK",
        };
      },
    });
    expect(resultado.data).toEqual({ model_name: "qwen", classes: [{ name: "Curso" }] });
  });
});
