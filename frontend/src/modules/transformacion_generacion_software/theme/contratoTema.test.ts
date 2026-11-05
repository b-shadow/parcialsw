import { describe, expect, it } from "vitest";

import { adaptarTemaV1AV2, calcularContraste, temaPredeterminadoV2, diagnosticosTemaLocal, normalizarBorradorTema, resolverRecetaDensidad, valorEjemplo } from "./contratoTema";

describe("contrato visual Flutter v2", () => {
  it("mantiene defaults accesibles y recetas deterministas", () => {
    expect(diagnosticosTemaLocal(temaPredeterminadoV2)).toEqual([]);
    expect(calcularContraste("#000000", "#FFFFFF")).toBe(21);
    expect(resolverRecetaDensidad("compact")).toEqual({ padding: 12, gap: 8, height: 44 });
  });

  it("detecta contraste invalido sin corregir silenciosamente", () => {
    const theme = structuredClone(temaPredeterminadoV2);
    theme.light.on_primary = theme.light.primary;
    expect(diagnosticosTemaLocal(theme)).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: "theme_contrast_insufficient", path: "light.primary/on_primary" })
    ]));
  });

  it("produce muestras segun el tipo real del manifiesto", () => {
    expect(valorEjemplo({ name: "fecha", logical_type: "date" })).toBe("2026-10-16");
    expect(valorEjemplo({ name: "cursoId", logical_type: "entity_id" })).toBe("Registro relacionado");
  });

  it("adapta v1 y normaliza igual que el contrato autoritativo", () => {
    const adapted = adaptarTemaV1AV2({ primary_color: "#0f766e", secondary_color: "#f59e0b", background_color: "#f8fafc", surface_color: "#ffffff", button_color: "#0f766e", font_family: "Inter", border_radius: 12, button_style: "outline", density: "comfortable" });
    const normalized = normalizarBorradorTema(adapted);
    expect(normalized.light.primary).toBe("#0F766E");
    expect(normalized.light.on_secondary).toBe("#000000");
    expect(normalized.typography.font_family).toBe("system");
    expect(normalized.shape.dialog_radius).toBe(12);
  });
});
