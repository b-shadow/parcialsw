export type UmlElementType = "class" | "interface" | "enum" | "abstract_class";
export type UmlVisibility = "public" | "private" | "protected" | "package";
export type UmlRelationshipType =
  | "association"
  | "inheritance"
  | "aggregation"
  | "composition"
  | "dependency"
  | "realization";

export type UmlDiagram = {
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

export type UmlClass = {
  id: string;
  diagram_id: string;
  name: string;
  visibility: UmlVisibility | string;
  element_type: UmlElementType | string;
  stereotype: string | null;
  description: string | null;
  metadata_json: Record<string, unknown>;
};

export type UmlVisualElement = {
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

export type UmlClassDetail = UmlClass & {
  attributes: UmlAttribute[];
  methods: UmlMethod[];
  visual: UmlVisualElement | null;
};

export type UmlAttribute = {
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

export type UmlMethod = {
  id: string;
  class_id: string;
  name: string;
  return_type: string | null;
  visibility: string;
  order_index: number;
  metadata_json: Record<string, unknown>;
  parameters: Array<{ id: string; name: string; data_type: string; default_value: string | null; order_index: number }>;
};

export type MethodRule = {
  code: string;
  description: string;
  severity: "info" | "warning" | "error";
  target?: { kind: "parameter" | "attribute" | "class" | "relationship"; id?: string | null; name: string } | null;
  error_code?: string | null;
  generation?: Record<string, unknown> | null;
};

export type MethodSideEffect = {
  code: string;
  kind: "data_change" | "status_change" | "notification" | "audit_event" | "refresh_required";
  description: string;
  target_entity_id: string | null;
  target_entity_name: string | null;
};

export type MethodRelatedEntity = {
  class_id: string | null;
  class_name: string;
  relation: "owner" | "input_reference" | "output" | "reads" | "creates" | "updates" | "deletes" | "refresh_target";
  required: boolean;
  source_parameter_id: string | null;
};

export type MethodSpecification = {
  id: string;
  method_id: string;
  description: string | null;
  operation_kind: "create" | "read" | "search" | "update" | "delete" | "calculate" | "business_action" | "custom";
  exposure: "internal" | "api" | "user_action";
  preconditions: MethodRule[];
  postconditions: MethodRule[];
  business_rules: MethodRule[];
  validations: MethodRule[];
  side_effects: MethodSideEffect[];
  required_permissions: Array<{ code: string; description?: string | null }>;
  related_entities: MethodRelatedEntity[];
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

export type MethodDiagnostic = {
  code: string;
  severity: "info" | "warning" | "error";
  path: string;
  message: string;
  suggestion: string | null;
  related_element_id: string | null;
};

export type MethodReadiness = {
  status: "empty" | "draft" | "needs_review" | "invalid" | "ready" | "legacy";
  ready_for_generation: boolean;
  errors: MethodDiagnostic[];
  warnings: MethodDiagnostic[];
  inferred_fields: string[];
};

export type MethodSpecificationEnvelope = {
  specification: MethodSpecification | null;
  readiness: MethodReadiness;
};

export type MethodSpecificationProposal = {
  action_id: string;
  method_id: string;
  base_revision: number;
  summary: string;
  patch: Partial<MethodSpecification>;
  changed_fields: string[];
  unresolved_references: string[];
  assumptions: string[];
  warnings: string[];
  validation: MethodReadiness;
  provider: string;
  fallback_used: boolean;
};

export type UmlRelationship = {
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

export type UmlValidation = {
  diagram_id: string;
  errors: string[];
  warnings: string[];
  recommendations: string[];
};

export type DiagramModel = {
  diagram: UmlDiagram;
  classes: UmlClassDetail[];
  relationships: UmlRelationship[];
};
