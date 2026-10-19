export type AiIntent =
  | "answer_question" | "explain_system" | "explain_uml" | "recommend"
  | "review_uml" | "validate_uml" | "modify_uml" | "generate_uml"
  | "specify_method" | "prepare_generation" | "summarize_conversation"
  | "summarize_project" | "coordinate_team" | "unknown";

export type { FlutterThemeConfig, FlutterThemeSettings } from "../../modules/transformacion_generacion_software/types/generation";

export type AiProjectSettings = {
  id: string;
  project_id: string;
  enabled: boolean;
  preferred_provider: "ollama" | "rule_engine";
  model_name: string;
  fallback_enabled: boolean;
  require_confirmation: boolean;
  max_context_messages: number;
  summary_trigger_messages: number;
  settings_json: Record<string, unknown>;
  created_by_user_id: string;
  updated_by_user_id: string;
  created_at: string;
  updated_at: string;
};

export type AiConversation = {
  id: string;
  project_id: string;
  title: string;
  created_by_user_id: string | null;
  status: "active" | "archived";
  summary: string | null;
  summary_until_sequence: number;
  last_message_sequence: number;
  schema_version: number;
  created_at: string;
  updated_at: string;
};

export type AiMessage = {
  id: string;
  conversation_id: string;
  project_id: string;
  author_user_id: string | null;
  author_display_name: string | null;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  sequence_number: number;
  client_message_id: string | null;
  correlation_id: string;
  status: "pending" | "streaming" | "completed" | "failed" | "cancelled";
  detected_intents: AiIntent[];
  references_json: Array<{ type: string; id: string; label: string }>;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AiMessagePage = {
  items: AiMessage[];
  previous_cursor: number | null;
  next_cursor: number | null;
  has_more_before: boolean;
  has_more_after: boolean;
  min_sequence: number | null;
  max_sequence: number | null;
};

export type AiAction = {
  id: string; project_id: string; conversation_id: string; source_message_id: string;
  requested_by_user_id: string; action_type: string; target_type: string | null;
  target_id: string | null; payload: Record<string, unknown>; risk_level: "low" | "medium" | "high";
  requires_confirmation: boolean;
  status: "proposed" | "confirmed" | "executing" | "applied" | "rejected" | "failed" | "cancelled";
  confirmed_by_user_id: string | null; confirmed_at: string | null; executed_at: string | null;
  result_json: Record<string, unknown>; error_message: string | null; idempotency_key: string;
  created_at: string; updated_at: string;
};

export type AiRecommendation = {
  id: string; project_id: string; conversation_id: string; source_message_id: string;
  category: string; severity: "info" | "warning" | "critical"; title: string; description: string;
  references_json: Array<{ type: string; id: string; label: string }>;
  status: "open" | "accepted" | "dismissed" | "resolved";
  resolved_by_user_id: string | null; resolved_at: string | null; resolution_note: string | null;
  created_at: string; updated_at: string;
};

export type AiInteractionRequest = {
  client_message_id: string;
  content: string;
  conversation_id?: string | null;
  diagram_id?: string | null;
  base_diagram_version?: number | null;
  requested_context?: {
    include_diagram?: boolean;
    include_recent_messages?: boolean;
    include_project_versions?: boolean;
  };
};

export type AiInteractionResponse = {
  message_id: string;
  correlation_id: string;
  status: "pending" | "streaming" | "completed" | "failed" | "cancelled";
  detected_intents: AiIntent[];
  answer: string;
  actions: AiAction[];
  recommendations: AiRecommendation[];
  conversation_sequence: number;
  provider: string;
  model: string;
  fallback_used: boolean;
  warnings: string[];
  requires_user_input: boolean;
  clarification_question: string | null;
  duration_ms: number;
  context_reduced: boolean;
};

export type AiProviderHealth = {
  provider: string;
  available: boolean;
  models: string[];
  selected_model: string;
  selected_model_available: boolean;
  latency_ms: number | null;
  error_code: string | null;
  error_message: string | null;
};

export type AiActionDecision = { action: AiAction; idempotent: boolean };

export type SpecificationRule = { code: string; description: string; severity: "info" | "warning" | "error" };
export type MethodSpecification = {
  id: string;
  method_id: string;
  description: string | null;
  operation_kind: "create" | "read" | "update" | "delete" | "search" | "calculate" | "business_action" | "custom";
  exposure: "internal" | "api" | "user_action";
  preconditions: SpecificationRule[];
  postconditions: SpecificationRule[];
  business_rules: SpecificationRule[];
  validations: SpecificationRule[];
  side_effects: SpecificationRule[];
  required_permissions: string[];
  related_entities: Array<{ class_id?: string; class_name: string; relation: string; required: boolean }>;
  backend_contract: Record<string, unknown> | null;
  frontend_contract: Record<string, unknown> | null;
  schema_version: number;
  created_at: string;
  updated_at: string;
};

export type MobileProjectSummary = {
  id: string; name: string; description: string | null; project_role: string; status: string;
  diagram_count: number; member_count: number; unread_notification_count: number; updated_at: string;
};

export type MobileDiagramSummary = {
  id: string; project_id: string; name: string; diagram_type: string; class_count: number;
  relationship_count: number; updated_at: string; updated_by_display_name: string | null;
};

export type MobileDiagramDetail = {
  diagram: Record<string, unknown>;
  classes: Array<Record<string, unknown>>;
  relationships: Array<Record<string, unknown>>;
  logical_version: number;
  can_read: boolean;
  can_edit: boolean;
};

export type ProjectSnapshotV2 = {
  schema_version: 2;
  captured_at: string;
  project: { id: string; name: string; description: string | null };
  diagrams: Array<Record<string, unknown>>;
  flutter_theme: { config: FlutterThemeConfig; preset_name: string | null; schema_version: number; revision: number } | null;
  generation_settings: Record<string, unknown>;
  ai_settings: Pick<AiProjectSettings, "enabled" | "preferred_provider" | "model_name" | "fallback_enabled" | "require_confirmation"> | null;
};

export type ProjectSocketEventV2 = {
  protocol_version: 2;
  type: "AI_MESSAGE_CREATED" | "AI_MESSAGE_STATUS_CHANGED" | "AI_ACTION_PROPOSED" |
    "AI_ACTION_STATUS_CHANGED" | "AI_RECOMMENDATION_CREATED" | "AI_RECOMMENDATION_STATUS_CHANGED" |
    "AI_CONVERSATION_SUMMARY_UPDATED" | "FLUTTER_THEME_UPDATED" |
    "PROJECT_VERSION_CREATED" | "PROJECT_VERSION_RESTORED" |
    "METHOD_SIGNATURE_UPDATED" | "METHOD_SPECIFICATION_CREATED" |
    "METHOD_SPECIFICATION_UPDATED" | "METHOD_SPECIFICATION_DELETED" |
    "METHOD_SPECIFICATION_REFINED" |
    "AI_PROCESSING_STARTED" | "AI_PROCESSING_FINISHED" | "AI_PROCESSING_FAILED" |
    "PRESENCE_JOINED" | "PRESENCE_LEFT" | "PRESENCE_SNAPSHOT" | "SYNC_REQUIRED";
  event_id: string;
  project_id: string;
  diagram_id?: string | null;
  sequence_number: number;
  conversation_sequence?: number | null;
  persistent?: boolean;
  correlation_id: string;
  occurred_at: string;
  actor: { user_id?: string | null; display_name: string };
  payload: Record<string, unknown>;
};

export type ProjectPresence = {
  user_id: string;
  display_name: string;
  project_role: string;
  connection_count: number;
  active_diagram_id?: string | null;
};
import type { FlutterThemeConfig } from "../../modules/transformacion_generacion_software/types/generation";

