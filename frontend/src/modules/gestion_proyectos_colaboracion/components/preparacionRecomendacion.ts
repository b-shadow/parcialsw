const requiredDecisions: Record<string, string> = {
  "Estados controlados":
    "Define los valores permitidos para cada estado antes de convertir el atributo String en un catálogo o enumeración.",
  "Reglas para calificaciones":
    "Define el rango permitido, la precisión y la nota mínima de aprobación antes de agregar las validaciones.",
  "Unicidad de la clase asociativa":
    "Indica qué combinación de referencias de la clase asociativa debe ser única para evitar registros duplicados.",
  "Clases sin estado definido":
    "Indica los atributos y tipos que necesita cada clase vacía.",
  "Modelo desconectado":
    "Indica qué clases se relacionan y las multiplicidades de cada extremo.",
  "Multiplicidades incompletas":
    "Indica la multiplicidad correcta en cada extremo de la relación.",
  "Completar reglas del dominio":
    "Define las precondiciones, validaciones y resultados esperados de los métodos.",
};

export function preparacionRecomendacion(title: string):
  | { kind: "automatic" }
  | { kind: "manual"; guidance: string } {
  if (title === "Identificadores ausentes") return { kind: "automatic" };
  return {
    kind: "manual",
    guidance: requiredDecisions[title] ??
      "Esta sugerencia necesita un cambio concreto definido por ti; aún no tiene una transformación automática segura.",
  };
}

export function solicitudCorreccionConCriterio(
  title: string,
  description: string,
  criterion: string,
  recommendationId?: string
): string {
  const identifier = recommendationId ? `\nID de recomendación: ${recommendationId}` : "";
  return `Corrige el diagrama siguiendo esta recomendación: ${title}. ${description}${identifier}\nMi criterio: ${criterion.trim()}\nPropón cambios UML concretos para que pueda revisarlos y confirmarlos. No apliques nada todavía.`;
}

// El identificador selecciona la recomendación en el motor; no es parte del texto público del chat.
export function contenidoVisibleMensajeIA(content: string): string {
  return content.replace(/^[ \t]*ID de recomendaci[oó]n:[ \t]*[0-9a-f-]{36}[ \t]*(?:\r?\n|$)/gim, "").trim();
}

export function esSugerenciaDeAtributos(title: string, description: string): boolean {
  return title === "Sugerencia de diseño" && /^Agregar atributos a [\p{L}\d_]+\.?$/iu.test(description.trim());
}
