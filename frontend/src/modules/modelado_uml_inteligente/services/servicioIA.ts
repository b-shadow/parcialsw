import { clienteApi } from "../../../core/api/cliente";

export type RespuestaUMLIA = {
  classes: Array<{
    name: string;
    stereotype?: string | null;
    attributes?: Array<{ name: string; data_type: string; visibility?: string | null; is_required?: boolean }>;
    methods?: Array<{ name: string; return_type?: string | null; visibility?: string | null }>;
  }>;
  relationships: Array<{
    source: string;
    target: string;
    relationship_type: string;
    label?: string | null;
    source_cardinality?: string | null;
    target_cardinality?: string | null;
    metadata_json?: Record<string, unknown>;
  }>;
  confidence: number;
  observations: string[];
  knowledge_context: string[];
  engine: string;
};

type AiValidationResponse = {
  errors: string[];
  warnings: string[];
  recommendations: string[];
  score: number;
  engine: string;
};

export const servicioIA = {
  async textToUml(prompt: string) {
    const response = await clienteApi.post<RespuestaUMLIA>("/ai/uml/text", {
      prompt,
      language: "es",
      source_type: "text"
    });
    return response.data;
  },
  async voiceToUml(payload: string | { transcript?: string; audio_base64?: string }) {
    const response = await clienteApi.post<RespuestaUMLIA>("/ai/uml/voice", {
      ...(typeof payload === "string" ? { transcript: payload } : payload),
      language: "es"
    });
    return response.data;
  },
  async imageToUml(payload: string | { description?: string; image_base64?: string; file_name?: string; project_id?: string }) {
    const response = await clienteApi.post<RespuestaUMLIA>("/ai/uml/image", {
      ...(typeof payload === "string" ? { description: payload } : payload),
      language: "es"
    });
    return response.data;
  },
  async validateModel(payload: Pick<RespuestaUMLIA, "classes" | "relationships">) {
    const response = await clienteApi.post<AiValidationResponse>("/ai/validate-model", payload);
    return response.data;
  },
  async modifyUml(payload: {
    instruction: string;
    classes: RespuestaUMLIA["classes"];
    relationships: RespuestaUMLIA["relationships"];
    selected_class_name?: string | null;
  }) {
    const response = await clienteApi.post<RespuestaUMLIA & { changes: string[] }>("/ai/uml/modify", payload);
    return response.data;
  },
  async knowledgeSearch(query: string) {
    const response = await clienteApi.post<Array<{ topic: string; content: string; tags: string[] }>>("/ai/knowledge/search", {
      query,
      limit: 3
    });
    return response.data;
  },
  async evaluation() {
    const response = await clienteApi.get<{
      dataset_size: number;
      class_precision: number;
      relationship_precision: number;
      average_score: number;
      offline: boolean;
    }>("/ai/evaluation/offline");
    return response.data;
  }
};
