import { describe, expect, it } from "vitest";

import { preparacionRecomendacion, solicitudCorreccionConCriterio } from "./preparacionRecomendacion";

describe("preparación de recomendaciones", () => {
  it("permite preparar identificadores como propuestas confirmables", () => {
    expect(preparacionRecomendacion("Identificadores ausentes")).toEqual({ kind: "automatic" });
  });

  it("explica los criterios que faltan para sugerencias de dominio", () => {
    for (const title of [
      "Estados controlados",
      "Reglas para calificaciones",
      "Unicidad de la clase asociativa",
    ]) {
      const result = preparacionRecomendacion(title);
      expect(result.kind).toBe("manual");
      if (result.kind === "manual") expect(result.guidance.length).toBeGreaterThan(30);
    }
  });

  it("no promete una transformación automática para sugerencias desconocidas", () => {
    expect(preparacionRecomendacion("Otra sugerencia").kind).toBe("manual");
  });

  it("incorpora el criterio del usuario y exige propuesta confirmable", () => {
    const prompt = solicitudCorreccionConCriterio(
      "Estados controlados",
      "Evita estados inconsistentes",
      "  Pendiente, Aprobado y Rechazado  "
    );
    expect(prompt).toContain("Estados controlados");
    expect(prompt).toContain("Mi criterio: Pendiente, Aprobado y Rechazado");
    expect(prompt).toContain("No apliques nada todavía");
  });
});
