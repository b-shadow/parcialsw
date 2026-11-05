export type Usuario = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_access_at: string | null;
  created_at: string;
  role_names: string[];
  status?: string;
};

export type Rol = {
  id: string;
  name: "ADMINISTRADOR" | "EDITOR";
  description: string | null;
  is_system: boolean;
};

export type RegistroAuditoria = {
  id: string;
  user_id: string | null;
  project_id: string | null;
  module: string;
  action: string;
  result: string;
  detail: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type CargaIngreso = {
  email: string;
  password: string;
};

export type CargaRegistro = CargaIngreso & {
  full_name: string;
};

export type RespuestaToken = {
  access_token: string;
  token_type: string;
};
