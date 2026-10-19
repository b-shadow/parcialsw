import { expect, test } from "@playwright/test";

test.use({ serviceWorkers: "block" });

const theme = {
  schema_version: 2, mode: "system",
  light: { primary: "#0F766E", on_primary: "#FFFFFF", secondary: "#2563EB", on_secondary: "#FFFFFF", background: "#F8FAFC", on_background: "#0F172A", surface: "#FFFFFF", on_surface: "#0F172A", error: "#B91C1C", on_error: "#FFFFFF", outline: "#64748B" },
  dark: { primary: "#5EEAD4", on_primary: "#042F2E", secondary: "#93C5FD", on_secondary: "#172554", background: "#020617", on_background: "#E2E8F0", surface: "#0F172A", on_surface: "#E2E8F0", error: "#FCA5A5", on_error: "#450A0A", outline: "#94A3B8" },
  typography: { font_family: "system", heading_font_family: "system", scale: "normal", weight: "regular" },
  shape: { button_radius: 8, input_radius: 8, card_radius: 8, dialog_radius: 8 },
  components: { button_style: "filled", input_style: "outline", card_style: "outlined", navigation_style: "automatic", density: "normal", show_field_labels: true },
};

const manifest = { schema_version: 1, source_hash: "1234567890abcdef", source_transformation_id: "tx1", supported_states: ["content", "loading", "empty", "error"], diagnostics: [], modules: [{ id: "inscripcion", name: "inscripcion", label: "Inscripcion academica con etiqueta extensa", icon: "folder", screens: [{ id: "inscripcion-form", kind: "form", title: "Formulario Inscripcion", fields: [
  { id: "estudiante", name: "estudianteId", label: "Estudiante con nombre y apellido excepcionalmente extensos", control: "entity_selector", required: true, logical_type: "entity_id" },
  { id: "curso", name: "cursoId", label: "Curso", control: "entity_selector", required: true, logical_type: "entity_id" },
  { id: "fecha", name: "fecha", label: "Fecha", control: "date_picker", required: true, logical_type: "date" }
], actions: [{ id: "inscribir", label: "Inscribir estudiante", interaction: "form", placement: "detail", confirmation_required: true, icon: "play" }] }] }, { id: "curso", name: "curso", label: "Cursos", icon: "folder", screens: [{ id: "curso-list", kind: "list", title: "Cursos", fields: [{ id: "nombre", name: "nombre", label: "Nombre", control: "text_input", required: true, logical_type: "string" }], actions: [] }] }] };

async function mockApi(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    if (url.endsWith("/auth/me")) return route.fulfill({ json: { id: "u1", email: "editor@example.com", full_name: "Editor UML", is_active: true, last_access_at: null, created_at: "2026-10-16", role_names: [] } });
    if (url.endsWith("/projects/p1")) return route.fulfill({ json: { id: "p1", name: "Academico", description: "", status: "active", owner_id: "u1", settings: {}, revision: 1, created_at: "2026-10-16", updated_at: "2026-10-16" } });
    if (url.includes("/uml/projects/p1/diagrams")) return route.fulfill({ json: [{ id: "d1", project_id: "p1", name: "Inscripciones", diagram_type: "class", description: "", metadata_json: {}, version: 1, created_at: "2026-10-16", updated_at: "2026-10-16" }] });
    if (url.endsWith("/generation/projects/p1/spring-boot")) return route.fulfill({ json: [{ id: "b1", project_id: "p1", transformation_id: "tx0", name: "Academico_v1", technology: "Spring Boot", language: "Java", database_engine: "PostgreSQL", version_label: "v1", status: "generated", artifact_path: "backend", manifest: { file_count: 24 }, created_at: "2026-10-16T10:00:00Z" }] });
    if (url.endsWith("/generation/projects/p1/flutter")) return route.fulfill({ json: [{ id: "f1", project_id: "p1", transformation_id: "tx1", backend_id: "b1", name: "Academico_v1", technology: "Flutter", language: "Dart", version_label: "v1", status: "generated", artifact_path: "flutter", manifest: { file_count: 18 }, created_at: "2026-10-16T11:00:00Z" }] });
    if (url.includes("/projects/p1/flutter-theme/presets")) return route.fulfill({ json: [] });
    if (url.endsWith("/projects/p1/flutter-theme")) return route.fulfill({ json: { id: "t1", project_id: "p1", theme, preset_name: null, revision: 2, diagnostics: [], normalized_fields: [], valid: true } });
    if (url.includes("/generation/transformations/tx1/ui-manifest")) return route.fulfill({ json: manifest });
    if (url.endsWith("/notifications/unread-count")) return route.fulfill({ json: { count: 0 } });
    if (url.includes("/notifications/push/config")) return route.fulfill({ json: { enabled: false, public_key: null } });
    return route.fulfill({ json: {} });
  });
}

for (const viewport of [{ name: "mobile", width: 390, height: 844 }, { name: "tablet", width: 768, height: 1024 }, { name: "desktop", width: 1440, height: 1000 }]) {
  test(`editor visual sin overflow en ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.addInitScript(() => localStorage.setItem("case_access_token", "e2e-token"));
    await mockApi(page);
    await page.goto("/proyectos/p1/generacion");
    await page.getByRole("button", { name: "Frontend Flutter" }).click();
    await expect(page.getByText("Creado para backend Academico_v1 (v1)")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Formulario Inscripcion" })).toBeVisible();
    await page.getByLabel("Escala de texto").selectOption("160");
    await page.getByRole("button", { name: "Oscuro", exact: true }).click();
    const editor = page.getByRole("region", { name: "Editor de estilos Flutter" });
    await expect(editor).toBeVisible();
    await expect(editor.getByText(/2 modulos$/)).toBeVisible();
    const navigationSelect = editor.getByRole("combobox", { name: "Navegacion", exact: true });
    await navigationSelect.selectOption("navigation_drawer");
    await expect(editor.getByRole("navigation", { name: "Navegacion lateral del preview" })).toBeVisible();
    await navigationSelect.selectOption("automatic");
    await expect(editor.getByRole("navigation", { name: "Navegacion inferior del preview" })).toBeVisible();
    const overflow = await editor.evaluate((element) => element.scrollWidth > element.clientWidth + 1);
    expect(overflow).toBe(false);
    if (viewport.name === "desktop") {
      await page.screenshot({ path: "test-results/project-generation-desktop.png", fullPage: true });
    }
    await page.addStyleTag({ content: "header.sticky, .fixed.bottom-5.right-5 { visibility: hidden !important; }" });
    await expect(editor).toHaveScreenshot(`phase6-${viewport.name}.png`, {
      animations: "disabled", maxDiffPixelRatio: 0.01,
    });
  });
}
