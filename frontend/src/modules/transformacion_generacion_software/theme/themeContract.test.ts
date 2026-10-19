import { describe, expect, it } from "vitest";

import { adaptThemeV1ToV2, calculateContrast, defaultThemeV2, localThemeDiagnostics, normalizeThemeDraft, resolveDensityRecipe, sampleValue } from "./themeContract";

describe("contrato visual Flutter v2", () => {
  it("mantiene defaults accesibles y recetas deterministas", () => {
    expect(localThemeDiagnostics(defaultThemeV2)).toEqual([]);
    expect(calculateContrast("#000000", "#FFFFFF")).toBe(21);
    expect(resolveDensityRecipe("compact")).toEqual({ padding: 12, gap: 8, height: 44 });
  });

  it("detecta contraste invalido sin corregir silenciosamente", () => {
    const theme = structuredClone(defaultThemeV2);
    theme.light.on_primary = theme.light.primary;
    expect(localThemeDiagnostics(theme)).toEqual(expect.arrayContaining([
      expect.objectContaining({ code: "theme_contrast_insufficient", path: "light.primary/on_primary" })
    ]));
  });

  it("produce muestras segun el tipo real del manifiesto", () => {
    expect(sampleValue({ name: "fecha", logical_type: "date" })).toBe("2026-10-16");
    expect(sampleValue({ name: "cursoId", logical_type: "entity_id" })).toBe("Registro relacionado");
  });

  it("adapta v1 y normaliza igual que el contrato autoritativo", () => {
    const adapted = adaptThemeV1ToV2({ primary_color: "#0f766e", secondary_color: "#f59e0b", background_color: "#f8fafc", surface_color: "#ffffff", button_color: "#0f766e", font_family: "Inter", border_radius: 12, button_style: "outline", density: "comfortable" });
    const normalized = normalizeThemeDraft(adapted);
    expect(normalized.light.primary).toBe("#0F766E");
    expect(normalized.light.on_secondary).toBe("#000000");
    expect(normalized.typography.font_family).toBe("system");
    expect(normalized.shape.dialog_radius).toBe(12);
  });
});
