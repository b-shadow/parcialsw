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

const project = {
  id: "p1",
  owner_id: "u1",
  name: "Sistema academico",
  description: "Modelo principal",
  status: "active",
  settings: {},
  revision: 0,
  created_at: "2026-10-19T10:00:00Z",
  updated_at: "2026-10-19T10:00:00Z"
};

const diagram = {
  id: "d1",
  project_id: "p1",
  created_by_user_id: "u1",
  name: "Sistema academico",
  diagram_type: "class",
  status: "active",
  current_version: 1,
  description: "Modelo principal",
  metadata_json: { project_diagram: true },
  created_at: "2026-10-19T10:00:00Z"
};

test("crear un proyecto abre su unico diagrama sin crear otro", async ({ page }) => {
  let diagramCreationRequests = 0;
  let projectCreationRequests = 0;
  let aiClassRequests = 0;
  let xmiImportRequests = 0;
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.addInitScript(() => localStorage.setItem("case_access_token", "e2e-token"));
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const method = route.request().method();
    if (url.endsWith("/auth/me")) return route.fulfill({ json: user });
    if (url.endsWith("/projects") && method === "POST") {
      projectCreationRequests += 1;
      return route.fulfill({ status: 201, json: project });
    }
    if (url.endsWith("/uml/projects/p1/diagrams")) return route.fulfill({ json: [diagram] });
    if (url.endsWith("/ai/uml/text") && method === "POST") {
      return route.fulfill({ json: {
        classes: [{ name: "Estudiante", attributes: [], methods: [] }],
        relationships: [], confidence: 0.95, observations: [], knowledge_context: [], engine: "e2e"
      } });
    }
    if (url.endsWith("/uml/diagrams/d1/classes") && method === "POST") {
      aiClassRequests += 1;
      return route.fulfill({ status: 201, json: {
        id: "c1", diagram_id: "d1", name: "Estudiante", visibility: "public",
        element_type: "class", stereotype: null, description: null, metadata_json: {}
      } });
    }
    if (url.endsWith("/uml/diagrams/d1/xmi/import") && method === "POST") {
      xmiImportRequests += 1;
      return route.fulfill({ json: diagram });
    }
    if (url.endsWith("/uml/diagrams") && method === "POST") {
      diagramCreationRequests += 1;
      return route.fulfill({ status: 409, json: { detail: { code: "PROJECT_DIAGRAM_ALREADY_EXISTS" } } });
    }
    if (url.endsWith("/uml/diagrams/d1/model")) {
      return route.fulfill({ json: { diagram, classes: [], relationships: [] } });
    }
    if (url.endsWith("/projects/p1/members")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/activity")) return route.fulfill({ json: { items: [], next_cursor: null, has_more: false, latest_sequence: 0 } });
    if (url.endsWith("/projects/p1/versions")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/ai/messages")) return route.fulfill({ json: { items: [], has_more_before: false, has_more_after: false, oldest_sequence: null, newest_sequence: null } });
    if (url.includes("/projects/p1/ai/actions") || url.includes("/projects/p1/ai/recommendations")) return route.fulfill({ json: [] });
    if (url.endsWith("/notifications/unread-count")) return route.fulfill({ json: { count: 0 } });
    if (url.includes("/notifications/push/config")) return route.fulfill({ json: { enabled: false, public_key: null } });
    return route.fulfill({ json: [] });
  });

  await page.goto("/proyectos/nuevo");

  await expect(page.getByRole("heading", { name: "Crear proyecto", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Crear desde IA" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Importar", exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/create-project.png", fullPage: true });

  await page.getByLabel("Nombre del proyecto").fill("Sistema academico");
  await page.getByLabel("Descripcion").fill("Modelo principal");
  await page.getByRole("button", { name: "Crear proyecto", exact: true }).click();

  await expect(page).toHaveURL(/\/proyectos\/p1\/uml\/d1$/);

  await page.goto("/proyectos/nuevo");
  await page.getByLabel("Nombre del proyecto").fill("Sistema academico");
  await page.getByLabel("Descripcion").fill("Modelo principal");
  await page.getByPlaceholder(/Sistema de ventas con clientes/).fill("Crear una clase Estudiante");
  await page.getByRole("button", { name: "Crear proyecto", exact: true }).click();
  await expect(page).toHaveURL(/\/proyectos\/p1\/uml\/d1$/);

  await page.goto("/proyectos/nuevo");
  await page.getByLabel("Nombre del proyecto").fill("Sistema importado");
  await page.getByLabel("Descripcion").fill("Modelo importado desde XMI");
  await page.locator('input[type="file"][accept*=".xmi"]').setInputFiles({
    name: "modelo.xmi",
    mimeType: "application/xml",
    buffer: Buffer.from('<?xml version="1.0"?><XMI/>')
  });
  await page.getByRole("button", { name: "Importar", exact: true }).click();
  await expect(page).toHaveURL(/\/proyectos\/p1\/uml\/d1$/);

  expect(diagramCreationRequests).toBe(0);
  expect(projectCreationRequests).toBe(3);
  expect(aiClassRequests).toBe(1);
  expect(xmiImportRequests).toBe(1);
});
