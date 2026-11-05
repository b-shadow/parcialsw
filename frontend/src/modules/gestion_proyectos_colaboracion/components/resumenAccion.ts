import type { AccionIA } from "../../../core/contracts/phase1";

const names: Record<string, string> = {
  create_class: "Crear clase",
  update_class: "Editar clase",
  delete_class: "Eliminar clase",
  create_attribute: "Agregar atributo",
  update_attribute: "Editar atributo",
  delete_attribute: "Eliminar atributo",
  create_method: "Agregar método",
  update_method: "Editar método",
  delete_method: "Eliminar método",
  create_relationship: "Crear relación",
  update_relationship: "Editar relación",
  delete_relationship: "Eliminar relación",
  update_method_specification: "Editar especificación",
  save_version: "Guardar versión",
};

export function resumenAccion(action: AccionIA): { title: string; details: string } {
  const payload = action.payload;
  const plan = payload._plan;
  const explanation = plan && typeof plan === "object" && !Array.isArray(plan)
    ? (plan as Record<string, unknown>).explanation
    : null;
  const fields = [
    typeof payload.class_name === "string" ? `Clase: ${payload.class_name}` : null,
    typeof payload.name === "string" ? `Nombre: ${payload.name}` : null,
    typeof payload.data_type === "string" ? `Tipo: ${payload.data_type}` : null,
    typeof payload.return_type === "string" ? `Retorno: ${payload.return_type}` : null,
    typeof payload.relationship_type === "string" ? `Relación: ${payload.relationship_type}` : null,
  ].filter(Boolean);
  return {
    title: names[action.action_type] ?? action.action_type.replace(/_/g, " "),
    details: typeof explanation === "string" && explanation.trim()
      ? explanation
      : fields.join(" · ") || (action.target_id ? `Elemento: ${action.target_id}` : "Revisa el cambio antes de confirmarlo"),
  };
}

export function dependenciasAccionListas(action: AccionIA, actions: AccionIA[]): boolean {
  const plan = action.payload._plan;
  if (!plan || typeof plan !== "object" || Array.isArray(plan)) return true;
  const keys = (plan as Record<string, unknown>).depends_on;
  if (!Array.isArray(keys)) return true;
  return keys.every((key) =>
    actions.some((candidate) => candidate.idempotency_key === key && candidate.status === "applied")
  );
}
