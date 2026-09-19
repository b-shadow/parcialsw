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
  version_number: number;
  name: string;
  description: string | null;
  snapshot: Record<string, unknown>;
  status: string;
  created_at: string;
};
