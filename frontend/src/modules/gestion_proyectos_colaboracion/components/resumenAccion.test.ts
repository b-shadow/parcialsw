import { describe, expect, it } from "vitest";
import type { AccionIA } from "../../../core/contracts/phase1";
import { dependenciasAccionListas, resumenAccion } from "./resumenAccion";

describe("actionSummary", () => {
  it("explica el cambio antes de aprobarlo", () => {
    const action = {
      action_type: "create_attribute",
      payload: { class_name: "Estudiante", name: "id", data_type: "UUID", _plan: {} },
    } as unknown as AccionIA;
    expect(resumenAccion(action)).toEqual({
      title: "Agregar atributo",
      details: "Clase: Estudiante · Nombre: id · Tipo: UUID",
    });
  });

  it("espera la aprobación de los cambios previos", () => {
    const previous = { idempotency_key: "first", status: "proposed" } as AccionIA;
    const next = { payload: { _plan: { depends_on: ["first"] } } } as unknown as AccionIA;
    expect(dependenciasAccionListas(next, [previous])).toBe(false);
    expect(dependenciasAccionListas(next, [{ ...previous, status: "applied" }])).toBe(true);
  });
});
