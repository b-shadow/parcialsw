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

export type FlutterThemeConfig = {
  primary_color: string;
  secondary_color: string;
  background_color: string;
  surface_color: string;
  button_color: string;
  font_family: string;
  border_radius: number;
  button_style: "filled" | "outline" | "tonal";
  density: "compact" | "normal" | "comfortable";
};

export type FrontendGenerationPayload = {
  transformation_id: string;
  name: string;
  version_label: string;
  backend_id?: string;
  api_base_url?: string;
  theme_config?: FlutterThemeConfig;
};
