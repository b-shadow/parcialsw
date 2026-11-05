export type Proyecto = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  status: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  revision: number;
};

export type IntegranteProyecto = {
  id: string;
  project_id: string;
  user_id: string;
  project_role: "ORGANIZADOR" | "EDITOR";
  joined_at: string;
  full_name: string | null;
  email: string | null;
};

export type CandidatoIntegranteProyecto = {
  id: string;
  full_name: string;
  email: string;
};

export type VersionProyecto = {
  id: string;
  project_id: string;
  created_by_user_id: string;
  version_number: number;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  created_by_name: string | null;
  kind: "manual" | "pre_restore_backup";
  snapshot_schema_version: number;
  snapshot_hash: string;
  snapshot_size_bytes: number;
  project_revision: number;
};

export type ResultadoRestauracionVersion = {
  restored_version: VersionProyecto;
  backup_version: VersionProyecto;
  restored_diagram_ids: string[];
  restore_operation_id: string;
  project_revision: number;
  idempotent_replay?: boolean;
};

export type VistaPreviaRestauracion = {
  version: VersionProyecto;
  current_revision: number;
  effective_schema_version: number;
  summary: Record<string, number>;
  differences: Record<string, number>;
  warnings: string[];
};

export type PaginaActividad = {
  items: CambioColaboracion[];
  next_cursor: number | null;
  has_more: boolean;
  latest_sequence: number;
};

export type CambioColaboracion = {
  id: string;
  project_id: string;
  diagram_id: string | null;
  user_id: string;
  user_name: string;
  client_event_id: string;
  sequence_number: number;
  event_type: string;
  element_type: string | null;
  element_id: string | null;
  base_version: number | null;
  payload: Record<string, unknown>;
  created_at: string;
  resource_type?: string | null;
  resource_id?: string | null;
  correlation_id?: string | null;
  causation_id?: string | null;
  summary_key?: string | null;
};
