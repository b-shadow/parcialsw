import { describe, expect, it } from "vitest";

import { contenidoVisibleMensajeIA, esSugerenciaDeAtributos, preparacionRecomendacion, solicitudCorreccionConCriterio } from "./preparacionRecomendacion";

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

  it("identifica la recomendación de diseño y conserva la clase de su descripción", () => {
    const prompt = solicitudCorreccionConCriterio(
      "Sugerencia de diseño",
      "Agregar atributos a Pago.",
      "añade nombre con valor string"
    );
    expect(prompt).toContain("Agregar atributos a Pago.");
    expect(prompt).not.toContain("ID de recomendación:");
    expect(contenidoVisibleMensajeIA(`${prompt}\nID de recomendación: 3d0d3465-3a17-4f93-91aa-35c3c6d6f041`)).not.toContain("ID de recomendación:");
    expect(contenidoVisibleMensajeIA(prompt)).toContain("Mi criterio: añade nombre con valor string");
    expect(esSugerenciaDeAtributos("Sugerencia de diseño", "Agregar atributos a Pago.")).toBe(true);
    expect(esSugerenciaDeAtributos("Estados controlados", "Agregar atributos a Pago.")).toBe(false);
  });
});
