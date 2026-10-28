export type PermissionCode =
  | "project.read"
  | "project.update"
  | "members.manage"
  | "uml.edit"
  | "versions.create"
  | "versions.restore"
  | "ai.chat"
  | "ai.confirm_actions"
  | "ai.settings"
  | "generation.run"
  | "theme.edit";

export const PERMISSION_CODES: readonly PermissionCode[] = [
  "project.read",
  "project.update",
  "members.manage",
  "uml.edit",
  "versions.create",
  "versions.restore",
  "ai.chat",
  "ai.confirm_actions",
  "ai.settings",
  "generation.run",
  "theme.edit",
] as const;

export type ProjectRole = "ORGANIZADOR" | "EDITOR" | "LECTOR";

export type MyMembership = {
  project_id: string;
  user_id: string;
  project_role: ProjectRole;
  permissions: PermissionCode[];
};

export type ChangeLogEntry = {
  id: string;
  project_id: string;
  occurred_at: string;
  actor_user_id: string | null;
  actor_display_name: string | null;
  source: "ui" | "ai" | "ws" | "system";
  module: string;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  diagram_id: string | null;
  summary: string;
  metadata: Record<string, unknown>;
};

export type ChangeLogPage = {
  items: ChangeLogEntry[];
  next_cursor: string | null;
  source: "redis" | "postgres_fallback";
};

export type InvitationStatus = "pending" | "accepted" | "rejected" | "revoked" | "expired";

export type ProjectInvitation = {
  id: string;
  project_id: string;
  project_name: string;
  invited_email: string;
  project_role: Exclude<ProjectRole, "ORGANIZADOR">;
  status: InvitationStatus;
  invited_by_name: string;
  expires_at: string;
  created_at: string;
};

export type ElementLock = {
  diagram_id: string;
  element_type: "class" | "relationship";
  element_id: string;
  locked_by: { user_id: string; display_name: string };
  expires_at: string;
};

export type AiProvider = "ollama" | "gemini" | "rule_engine";
