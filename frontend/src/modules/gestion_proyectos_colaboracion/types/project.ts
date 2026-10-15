export type Project = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  status: string;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type ProjectMember = {
  id: string;
  project_id: string;
  user_id: string;
  project_role: "ORGANIZADOR" | "EDITOR";
  joined_at: string;
};

export type ProjectVersion = {
  id: string;
  project_id: string;
  created_by_user_id: string;
  version_number: number;
  name: string;
  description: string | null;
  snapshot: Record<string, unknown>;
  status: string;
  created_at: string;
  created_by_name: string | null;
};

export type VersionRestoreResult = {
  restored_version: ProjectVersion;
  backup_version: ProjectVersion;
  restored_diagram_ids: string[];
};

export type CollaborationChange = {
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
};
