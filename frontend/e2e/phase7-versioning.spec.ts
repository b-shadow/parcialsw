import { expect, test } from "@playwright/test";

test.use({ serviceWorkers: "block" });

const user = { id: "u1", email: "owner@example.com", full_name: "Propietario", is_active: true, last_access_at: null, created_at: "2026-10-16T10:00:00Z", role_names: [] };
const project = { id: "p1", owner_id: "u1", name: "Sistema academico", description: "Modelo colaborativo", status: "active", settings: {}, revision: 8, created_at: "2026-10-16T10:00:00Z", updated_at: "2026-10-16T10:00:00Z" };
const diagram = { id: "d1", project_id: "p1", created_by_user_id: "u1", name: "Sistema academico", diagram_type: "class", status: "active", current_version: 1, description: "Modelo colaborativo", metadata_json: {}, created_at: "2026-10-16T10:00:00Z" };
const version = { id: "v1", project_id: "p1", created_by_user_id: "u1", version_number: 3, name: "Entrega estable", description: "Antes de cambios", snapshot: {}, status: "available", created_at: "2026-10-16T10:00:00Z", created_by_name: "Propietario", kind: "manual", snapshot_schema_version: 2, snapshot_hash: "a".repeat(64), snapshot_size_bytes: 900, project_revision: 7 };

test("organizador guarda e inspecciona una version sin salir del proyecto", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.addInitScript(() => localStorage.setItem("case_access_token", "e2e-token"));
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/auth/me")) return route.fulfill({ json: user });
    if (url.endsWith("/projects/p1/members")) return route.fulfill({ json: [{ id: "m1", project_id: "p1", user_id: "u1", project_role: "ORGANIZADOR", joined_at: "2026-10-16T10:00:00Z" }] });
    if (url.includes("/uml/projects/p1/diagrams")) return route.fulfill({ json: [diagram] });
    if (url.endsWith("/uml/diagrams/d1/model")) return route.fulfill({ json: { diagram, classes: [], relationships: [] } });
    if (url.includes("/projects/p1/ai/messages")) return route.fulfill({ json: { items: [], has_more_before: false, has_more_after: false, oldest_sequence: null, newest_sequence: null } });
    if (url.includes("/projects/p1/ai/actions")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/ai/recommendations")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/changes")) return route.fulfill({ json: [] });
    if (url.includes("/projects/p1/activity")) return route.fulfill({ json: { items: [{ id: "e1", project_id: "p1", diagram_id: null, user_id: "u1", user_name: "Propietario", client_event_id: "c1", sequence_number: 9, event_type: "PROJECT_VERSION_CREATED", element_type: "project_version", element_id: "v1", base_version: null, payload: {}, created_at: "2026-10-16T10:00:00Z", resource_type: "project_version" }], next_cursor: null, has_more: false, latest_sequence: 9 } });
    if (url.endsWith("/projects/p1/versions") && route.request().method() === "GET") return route.fulfill({ json: [version] });
    if (url.endsWith("/projects/p1/versions") && route.request().method() === "POST") return route.fulfill({ status: 200, json: { ...version, id: "v2", version_number: 4, name: "Revision final", project_revision: 8 } });
    if (url.includes("/projects/p1/versions/v1/restore-preview")) return route.fulfill({ json: { version, current_revision: 8, effective_schema_version: 2, summary: { diagrams: 2, classes: 5, attributes: 12, methods: 4, relationships: 3 }, differences: { diagrams: 0, classes: -1, attributes: 0, methods: 0, relationships: 1 }, warnings: [] } });
    if (url.endsWith("/projects/p1")) return route.fulfill({ json: project });
    if (url.endsWith("/notifications/unread-count")) return route.fulfill({ json: { count: 0 } });
    if (url.includes("/notifications/push/config")) return route.fulfill({ json: { enabled: false, public_key: null } });
    return route.fulfill({ json: { items: [], next_cursor: null, has_more: false } });
  });

  await page.goto("/proyectos/p1/uml/d1");
  await page.getByRole("tab", { name: "Versiones", exact: true }).click();
  await expect(page.getByText("Propietario").last()).toBeVisible();
  await page.locator('[role="tabpanel"]:visible').getByRole("button", { name: "Versiones", exact: true }).click();
  await expect(page.getByText("v3 · Entrega estable")).toBeVisible();
  await page.locator("aside").getByRole("button", { name: "Guardar version" }).click();
  await page.getByLabel("Nombre", { exact: true }).fill("Revision final");
  await page.getByRole("button", { name: "Guardar", exact: true }).click();
  await expect(page.getByText("Version 4 guardada.")).toBeVisible();
  await page.getByRole("button", { name: "Restaurar version 3" }).click();
  await expect(page.getByRole("dialog")).toContainText("Se creara un respaldo automatico");
  await expect(page.getByRole("dialog")).toContainText("12");
});
