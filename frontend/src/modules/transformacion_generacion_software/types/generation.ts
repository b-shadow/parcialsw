export type Transformation = {
  id: string;
  project_id: string;
  diagram_id: string;
  requested_by_user_id: string;
  source_version: string | null;
  target_platform: "spring_boot" | "flutter" | "full_stack";
  intermediate_model: Record<string, unknown>;
  status: string;
  created_at: string;
};

export type GeneratedBackend = {
  id: string;
  project_id: string;
  transformation_id: string;
  name: string;
  technology: string;
  language: string;
  database_engine: string;
  version_label: string;
  status: string;
  artifact_path: string | null;
  manifest: {
    file_count?: number;
    entity_count?: number;
    generated_layers?: string[];
    zip_path?: string;
    [key: string]: unknown;
  };
  created_at: string;
};

export type GeneratedFrontend = {
  id: string;
  project_id: string;
  transformation_id: string;
  backend_id: string | null;
  name: string;
  technology: string;
  language: string;
  version_label: string;
  status: string;
  artifact_path: string | null;
  manifest: {
    file_count?: number;
    entity_count?: number;
    generated_layers?: string[];
    zip_path?: string;
    package_name?: string;
    api_base_url?: string;
    [key: string]: unknown;
  };
  created_at: string;
};

export type ThemePalette = {
  primary: string; on_primary: string; secondary: string; on_secondary: string;
  background: string; on_background: string; surface: string; on_surface: string;
  error: string; on_error: string; outline: string;
};

export type FlutterThemeConfig = {
  schema_version: 2;
  mode: "light" | "dark" | "system";
  light: ThemePalette;
  dark: ThemePalette;
  typography: {
    font_family: "system";
    heading_font_family: "system";
    scale: "compact" | "normal" | "large";
    weight: "regular" | "medium";
  };
  shape: { button_radius: number; input_radius: number; card_radius: number; dialog_radius: number };
  components: {
  button_style: "filled" | "outline" | "tonal";
    input_style: "outline" | "filled";
    card_style: "flat" | "outlined" | "elevated";
    navigation_style: "bottom_bar" | "navigation_drawer" | "automatic";
  density: "compact" | "normal" | "comfortable";
    show_field_labels: boolean;
  };
};

export type FlutterThemeConfigV1 = {
  primary_color: string; secondary_color: string; background_color: string; surface_color: string;
  button_color: string; font_family: string; border_radius: number;
  button_style: "filled" | "outline" | "tonal"; density: "compact" | "normal" | "comfortable";
};
export type FlutterThemeInput = FlutterThemeConfig | FlutterThemeConfigV1;

export type ThemeDiagnostic = { code: string; severity: "warning" | "error"; path: string; message: string; suggestion?: string; actual?: number; required?: number };
export type FlutterThemeSettings = { id: string | null; project_id: string; theme: FlutterThemeConfig; preset_name: string | null; revision: number; diagnostics: ThemeDiagnostic[]; normalized_fields: string[]; valid: boolean };
export type FlutterThemePreset = { id: string; kind: "system" | "custom"; name: string; description: string | null; config: FlutterThemeConfig; schema_version: 2; updated_at: string | null };
export type UiManifestField = { id: string; name: string; label: string; control: string; required: boolean; logical_type: string };
export type UiManifestScreen = { id: string; kind: "list" | "detail" | "form" | "filter" | "action"; title: string; fields: UiManifestField[]; actions: Array<{ id: string; label: string; interaction: string; placement: string; confirmation_required: boolean; icon: string }> };
export type UiManifest = { schema_version: 1; source_hash: string; source_transformation_id: string | null; modules: Array<{ id: string; name: string; label: string; icon: string; screens: UiManifestScreen[] }>; supported_states: string[]; diagnostics: PlanDiagnostic[] };

export type FrontendGenerationPayload = {
  transformation_id: string;
  name: string;
  version_label: string;
  backend_id?: string;
  api_base_url?: string;
  theme_config?: FlutterThemeInput;
};

export type PlanDiagnostic = {
  code: string;
  severity: "warning" | "error";
  message: string;
  suggestion?: string | null;
  method_id?: string | null;
  class_id?: string | null;
  path?: string | null;
};

export type GenerationPreflight = {
  schema_version: number;
  canonical_hash: string;
  ready: boolean;
  errors: PlanDiagnostic[];
  plan: {
    diagnostics?: PlanDiagnostic[];
    operations?: unknown[];
    routes?: unknown[];
    [key: string]: unknown;
  };
  ui_manifest: UiManifest;
};

export type CoordinatedGeneration = {
  id: string;
  project_id: string;
  transformation_id: string;
  requested_by_user_id: string;
  client_request_id: string;
  name: string;
  status: "verified" | "generated_unverified" | "failed" | "generating";
  stage: string;
  plan_hash: string | null;
  diagnostics: PlanDiagnostic[];
  manifest: Record<string, unknown>;
  artifact_path: string | null;
  error_detail: string | null;
  created_at: string;
};
