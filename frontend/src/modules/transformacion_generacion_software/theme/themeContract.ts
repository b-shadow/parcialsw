import type { FlutterThemeConfig, FlutterThemeConfigV1, ThemeDiagnostic, ThemePalette, UiManifest, UiManifestScreen } from "../types/generation";

export const defaultThemeV2: FlutterThemeConfig = {
  schema_version: 2, mode: "system",
  light: { primary: "#0F766E", on_primary: "#FFFFFF", secondary: "#2563EB", on_secondary: "#FFFFFF", background: "#F8FAFC", on_background: "#0F172A", surface: "#FFFFFF", on_surface: "#0F172A", error: "#B91C1C", on_error: "#FFFFFF", outline: "#64748B" },
  dark: { primary: "#5EEAD4", on_primary: "#042F2E", secondary: "#93C5FD", on_secondary: "#172554", background: "#020617", on_background: "#E2E8F0", surface: "#0F172A", on_surface: "#E2E8F0", error: "#FCA5A5", on_error: "#450A0A", outline: "#94A3B8" },
  typography: { font_family: "system", heading_font_family: "system", scale: "normal", weight: "regular" },
  shape: { button_radius: 8, input_radius: 8, card_radius: 8, dialog_radius: 8 },
  components: { button_style: "filled", input_style: "outline", card_style: "outlined", navigation_style: "automatic", density: "normal", show_field_labels: true }
};

function readableOn(background: string) {
  return calculateContrast(background, "#000000") >= calculateContrast(background, "#FFFFFF") ? "#000000" : "#FFFFFF";
}

export function adaptThemeV1ToV2(input: FlutterThemeConfigV1): FlutterThemeConfig {
  const theme = structuredClone(defaultThemeV2);
  theme.light.primary = input.primary_color.toUpperCase();
  theme.light.on_primary = readableOn(theme.light.primary);
  theme.light.secondary = input.secondary_color.toUpperCase();
  theme.light.on_secondary = readableOn(theme.light.secondary);
  theme.light.background = input.background_color.toUpperCase();
  theme.light.on_background = readableOn(theme.light.background);
  theme.light.surface = input.surface_color.toUpperCase();
  theme.light.on_surface = readableOn(theme.light.surface);
  theme.typography.font_family = "system";
  theme.typography.heading_font_family = "system";
  theme.shape = { button_radius: input.border_radius, input_radius: input.border_radius, card_radius: input.border_radius, dialog_radius: input.border_radius };
  theme.components.button_style = input.button_style;
  theme.components.density = input.density;
  return theme;
}

export function normalizeThemeDraft(input: FlutterThemeConfig): FlutterThemeConfig {
  const theme = structuredClone(input);
  (["light", "dark"] as const).forEach((mode) => {
    (Object.keys(theme[mode]) as Array<keyof ThemePalette>).forEach((token) => { theme[mode][token] = theme[mode][token].trim().toUpperCase(); });
  });
  (Object.keys(theme.shape) as Array<keyof FlutterThemeConfig["shape"]>).forEach((token) => {
    theme.shape[token] = Math.max(0, Math.min(24, Math.round(theme.shape[token])));
  });
  return theme;
}

export function resolveColorModeTokens(theme: FlutterThemeConfig, mode: "light" | "dark"): ThemePalette {
  return theme[mode];
}

function channel(value: number) { const ratio = value / 255; return ratio <= 0.04045 ? ratio / 12.92 : ((ratio + 0.055) / 1.055) ** 2.4; }
export function calculateContrast(first: string, second: string) {
  const luminance = (color: string) => { const values = [1, 3, 5].map((index) => Number.parseInt(color.slice(index, index + 2), 16)); return 0.2126 * channel(values[0]) + 0.7152 * channel(values[1]) + 0.0722 * channel(values[2]); };
  const values = [luminance(first), luminance(second)];
  return (Math.max(...values) + 0.05) / (Math.min(...values) + 0.05);
}

export function localThemeDiagnostics(theme: FlutterThemeConfig): ThemeDiagnostic[] {
  const diagnostics: ThemeDiagnostic[] = [];
  (["light", "dark"] as const).forEach((mode) => {
    const palette = theme[mode];
    (Object.keys(palette) as Array<keyof ThemePalette>).forEach((token) => {
      if (!/^#[0-9A-F]{6}$/i.test(palette[token])) diagnostics.push({ code: "theme_color_invalid", severity: "error", path: `${mode}.${token}`, message: "Use un color hexadecimal #RRGGBB." });
    });
    (["primary", "secondary", "background", "surface", "error"] as const).forEach((token) => {
      const foreground = `on_${token}` as keyof ThemePalette;
      if (!/^#[0-9A-F]{6}$/i.test(palette[token]) || !/^#[0-9A-F]{6}$/i.test(palette[foreground])) return;
      const ratio = calculateContrast(palette[token], palette[foreground]);
      if (ratio < 4.5) diagnostics.push({ code: "theme_contrast_insufficient", severity: "error", path: `${mode}.${token}/${String(foreground)}`, actual: Number(ratio.toFixed(2)), required: 4.5, message: `Contraste ${ratio.toFixed(2)}:1; se requiere 4.5:1.` });
    });
    const outline = /^#[0-9A-F]{6}$/i.test(palette.outline) && /^#[0-9A-F]{6}$/i.test(palette.surface) ? calculateContrast(palette.outline, palette.surface) : 3;
    if (outline < 3) diagnostics.push({ code: "theme_outline_contrast_insufficient", severity: "error", path: `${mode}.outline/surface`, actual: Number(outline.toFixed(2)), required: 3, message: `El borde requiere contraste 3:1.` });
  });
  return diagnostics;
}

export function resolveDensityRecipe(value: FlutterThemeConfig["components"]["density"]) {
  return value === "compact" ? { padding: 12, gap: 8, height: 44 } : value === "comfortable" ? { padding: 20, gap: 16, height: 52 } : { padding: 16, gap: 12, height: 48 };
}

export function sampleValue(field: { name: string; logical_type: string }) {
  if (field.logical_type === "date") return "2026-10-16";
  if (field.logical_type === "datetime") return "2026-10-16 10:30";
  if (field.logical_type === "boolean") return "Activo";
  if (["integer", "decimal"].includes(field.logical_type)) return "25";
  if (field.logical_type === "entity_id" || field.name.toLowerCase().endsWith("id")) return "Registro relacionado";
  return `${field.name} de ejemplo`;
}

export function firstPreviewScreen(manifest: UiManifest | null): UiManifestScreen | null {
  return manifest?.modules[0]?.screens[0] ?? null;
}
