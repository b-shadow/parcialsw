import { describe, expect, it } from "vitest";

import { notificationPath } from "./notificationService";

describe("notificationPath", () => {
  it("resuelve destinos internos de proyecto y conserva parametros permitidos", () => {
    expect(notificationPath({
      route_name: "project_collaborative",
      params: { project_id: "project-1" },
      query: { panel: "versions", version_id: "version-2" }
    })).toBe("/proyectos/project-1/colaborativo?panel=versions&version_id=version-2");
  });

  it("rechaza de forma segura rutas no conocidas", () => {
    expect(notificationPath({ route_name: "https://attacker.example" })).toBe("/proyectos");
  });
});
