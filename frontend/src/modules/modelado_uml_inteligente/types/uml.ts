export type TipoElementoUML = "class" | "interface" | "enum" | "abstract_class";
export type VisibilidadUML = "public" | "private" | "protected" | "package";
export type TipoRelacionUML =
  | "association"
  | "inheritance"
  | "aggregation"
  | "composition"
  | "dependency"
  | "realization";

export type DiagramaUML = {
  id: string;
  project_id: string;
  created_by_user_id: string;
  name: string;
  diagram_type: string;
  status: string;
  current_version: number;
  description: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type ClaseUML = {
  id: string;
  diagram_id: string;
  name: string;
  visibility: VisibilidadUML | string;
  element_type: TipoElementoUML | string;
  stereotype: string | null;
  description: string | null;
  metadata_json: Record<string, unknown>;
};

export type ElementoVisualUML = {
  id: string;
  diagram_id: string;
  element_type: string;
  element_id: string;
  position_x: number;
  position_y: number;
  width: number | null;
  height: number | null;
  style: Record<string, unknown>;
};

export type DetalleClaseUML = ClaseUML & {
  attributes: AtributoUML[];
  methods: MetodoUML[];
  visual: ElementoVisualUML | null;
};

export type AtributoUML = {
  id: string;
  class_id: string;
  name: string;
  data_type: string;
  visibility: string;
  initial_value: string | null;
  multiplicity: string | null;
  is_required: boolean;
  order_index: number;
  constraints: Record<string, unknown>;
};

export type MetodoUML = {
  id: string;
  class_id: string;
  name: string;
  return_type: string | null;
  visibility: string;
  order_index: number;
  metadata_json: Record<string, unknown>;
  parameters: Array<{ id: string; name: string; data_type: string; default_value: string | null; order_index: number }>;
};

export type ReglaMetodo = {
  code: string;
  description: string;
  severity: "info" | "warning" | "error";
  target?: { kind: "parameter" | "attribute" | "class" | "relationship"; id?: string | null; name: string } | null;
  error_code?: string | null;
  generation?: Record<string, unknown> | null;
};

export type EfectoSecundarioMetodo = {
  code: string;
  kind: "data_change" | "status_change" | "notification" | "audit_event" | "refresh_required";
  description: string;
  target_entity_id: string | null;
  target_entity_name: string | null;
};

export type EntidadRelacionadaMetodo = {
  class_id: string | null;
  class_name: string;
  relation: "owner" | "input_reference" | "output" | "reads" | "creates" | "updates" | "deletes" | "refresh_target";
  required: boolean;
  source_parameter_id: string | null;
};

export type EspecificacionMetodo = {
  id: string;
  method_id: string;
  description: string | null;
  operation_kind: "create" | "read" | "search" | "update" | "delete" | "calculate" | "business_action" | "custom";
  exposure: "internal" | "api" | "user_action";
  preconditions: ReglaMetodo[];
  postconditions: ReglaMetodo[];
  business_rules: ReglaMetodo[];
  validations: ReglaMetodo[];
  side_effects: EfectoSecundarioMetodo[];
  required_permissions: Array<{ code: string; description?: string | null }>;
  related_entities: EntidadRelacionadaMetodo[];
  backend_contract: {
    http_method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
    path: string;
    request_dto: string | null;
    response_dto: string | null;
    transactional: boolean;
    authorization: string[];
    error_codes: string[];
    status_codes: { success: number; validation_error: number; not_found: number; conflict: number };
  } | null;
  frontend_contract: {
    interaction: "form" | "button" | "menu_action" | "background" | "filter";
    label: string;
    placement: string | null;
    confirmation_required: boolean;
    refresh_targets: string[];
    success_message: string | null;
    fields: Array<{
      parameter_id: string | null;
      parameter: string;
      control: string;
      source_entity_id: string | null;
      source_entity: string | null;
      display_fields: string[];
      hidden: boolean;
    }>;
  } | null;
  schema_version: 1;
  revision: number;
  created_at: string;
  updated_at: string;
};

export type DiagnosticoMetodo = {
  code: string;
  severity: "info" | "warning" | "error";
  path: string;
  message: string;
  suggestion: string | null;
  related_element_id: string | null;
};

export type PreparacionMetodo = {
  status: "empty" | "draft" | "needs_review" | "invalid" | "ready" | "legacy";
  ready_for_generation: boolean;
  errors: DiagnosticoMetodo[];
  warnings: DiagnosticoMetodo[];
  inferred_fields: string[];
};

export type EnvolturaEspecificacionMetodo = {
  specification: EspecificacionMetodo | null;
  readiness: PreparacionMetodo;
};

export type PropuestaEspecificacionMetodo = {
  action_id: string;
  method_id: string;
  base_revision: number;
  summary: string;
  patch: Partial<EspecificacionMetodo>;
  changed_fields: string[];
  unresolved_references: string[];
  assumptions: string[];
  warnings: string[];
  validation: PreparacionMetodo;
  provider: string;
  fallback_used: boolean;
};

export type RelacionUML = {
  id: string;
  diagram_id: string;
  source_class_id: string;
  target_class_id: string;
  relationship_type: string;
  source_cardinality: string | null;
  target_cardinality: string | null;
  direction: string;
  label: string | null;
  metadata_json: Record<string, unknown>;
};

export type ValidacionUML = {
  diagram_id: string;
  errors: string[];
  warnings: string[];
  recommendations: string[];
};

export type ModeloDiagrama = {
  diagram: DiagramaUML;
  classes: DetalleClaseUML[];
  relationships: RelacionUML[];
};
