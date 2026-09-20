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
  visibility: string;
  element_type: string;
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
