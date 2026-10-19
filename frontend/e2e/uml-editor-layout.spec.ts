import { expect, test } from "@playwright/test";

test.use({ serviceWorkers: "block" });

const user = {
  id: "u1",
  email: "editor@example.com",
  full_name: "Editor UML",
  is_active: true,
  last_access_at: null,
  created_at: "2026-10-19T10:00:00Z",
  role_names: []
};

const diagramModel = {
  diagram: {
    id: "d1",
    project_id: "p1",
    name: "Inscripciones",
    diagram_type: "class",
    description: "Modelo academico",
    metadata_json: {},
    version: 1,
    created_at: "2026-10-19T10:00:00Z",
    updated_at: "2026-10-19T10:00:00Z"
  },
  classes: [
    {
      id: "c1", diagram_id: "d1", name: "Estudiante", visibility: "public", element_type: "class",
      stereotype: null, description: null, metadata_json: {},
      attributes: [{ id: "a1", class_id: "c1", name: "id", data_type: "UUID", visibility: "private", initial_value: null, multiplicity: null, is_required: true, order_index: 0, constraints: {} }],
      methods: [{ id: "m1", class_id: "c1", name: "inscribirse", return_type: "void", visibility: "public", order_index: 0, metadata_json: {}, parameters: [] }],
      visual: { id: "v1", diagram_id: "d1", element_type: "class", element_id: "c1", position_x: 120, position_y: 130, width: 290, height: 130, style: {} }
    },
    {
      id: "c2", diagram_id: "d1", name: "Curso", visibility: "public", element_type: "class",
      stereotype: null, description: null, metadata_json: {}, attributes: [], methods: [],
      visual: { id: "v2", diagram_id: "d1", element_type: "class", element_id: "c2", position_x: 470, position_y: 130, width: 290, height: 100, style: {} }
    }
  ],
  relationships: [{
    id: "r1", diagram_id: "d1", source_class_id: "c1", target_class_id: "c2",
    relationship_type: "aggregation", source_cardinality: "0..*", target_cardinality: "1",
    direction: "source_to_target", label: "cursa", metadata_json: {}
  }]
};

test("editor UML presenta herramientas compactas sin alterar el lienzo", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => localStorage.setItem("case_access_token", "e2e-token"));
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/auth/me")) return route.fulfill({ json: user });
    if (url.endsWith("/uml/diagrams/d1/model")) return route.fulfill({ json: diagramModel });
    if (url.endsWith("/projects/p1/members")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/activity")) return route.fulfill({ json: { items: [], next_cursor: null, has_more: false, latest_sequence: 0 } });
    if (url.endsWith("/projects/p1/versions")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/ai/messages")) return route.fulfill({ json: { items: [], has_more_before: false, has_more_after: false, oldest_sequence: null, newest_sequence: null } });
    if (url.includes("/projects/p1/ai/actions")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/ai/recommendations")) return route.fulfill({ json: [] });
    if (url.endsWith("/notifications/unread-count")) return route.fulfill({ json: { count: 0 } });
    if (url.includes("/notifications/push/config")) return route.fulfill({ json: { enabled: false, public_key: null } });
    return route.fulfill({ json: [] });
  });

  await page.goto("/proyectos/p1/uml/d1");

  await expect(page.getByRole("heading", { name: "Editor UML" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Editor" })).toHaveAttribute("aria-selected", "true");
  for (const tool of ["Select", "Clase", "Asociacion", "Generalize", "Association Class", "Compose", "Aggregate"]) {
    await expect(page.getByRole("button", { name: tool, exact: true })).toBeVisible();
  }
  const toolRows = await Promise.all(
    ["Select", "Clase", "Asociacion", "Generalize", "Association Class", "Compose", "Aggregate"].map(
      async (tool) => (await page.getByRole("button", { name: tool, exact: true }).boundingBox())?.y
    )
  );
  expect(toolRows[0]).toBe(toolRows[1]);
  expect(toolRows[2]).toBe(toolRows[3]);
  expect(toolRows[3]).toBe(toolRows[4]);
  expect(toolRows[5]).toBe(toolRows[6]);
  expect(toolRows[2]!).toBeGreaterThan(toolRows[0]!);
  expect(toolRows[5]!).toBeGreaterThan(toolRows[2]!);
  await expect(page.locator('input[value="Estudiante"]')).toBeVisible();
  await expect(page.locator('input[value="Curso"]')).toBeVisible();
  await expect(page.getByRole("heading", { name: "Propiedades del elemento" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Agregar atributo", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Agregar metodo", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Relaciones", exact: true }).click();
  await expect(page.getByText("Relaciones del diagrama", { exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "aggregation", exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Propiedades del elemento", exact: true }).click();

  await page.getByRole("tab", { name: "Asistente" }).click();
  await expect(page.getByText("Asistente del proyecto", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Versiones" }).click();
  await expect(page.getByText("Actividad del proyecto", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Editor" }).click();
  await expect(page.getByText("Elementos del diagrama", { exact: true })).toBeVisible();

  const editor = page.locator(".uml-editor-scope");
  expect(await editor.evaluate((element) => element.scrollWidth > element.clientWidth + 1)).toBe(false);
  await page.screenshot({ path: "test-results/uml-editor-redesign.png", fullPage: true });
});
