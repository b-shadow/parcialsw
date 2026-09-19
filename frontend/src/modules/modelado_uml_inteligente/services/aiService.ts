import { apiClient } from "../../../core/api/client";

type AiUmlResponse = {
  classes: Array<{ name: string }>;
  relationships: Array<{ source: string; target: string; relationship_type: string }>;
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

export const aiService = {
  async textToUml(prompt: string) {
    const response = await apiClient.post<AiUmlResponse>("/ai/uml/text", {
      prompt,
      language: "es",
      source_type: "text"
    });
    return response.data;
  },
  async voiceToUml(transcript: string) {
    const response = await apiClient.post<AiUmlResponse>("/ai/uml/voice", {
      transcript,
      language: "es"
    });
    return response.data;
  },
  async imageToUml(description: string) {
    const response = await apiClient.post<AiUmlResponse>("/ai/uml/image", {
      description,
      language: "es"
    });
    return response.data;
  },
  async validateModel(payload: Pick<AiUmlResponse, "classes" | "relationships">) {
    const response = await apiClient.post<AiValidationResponse>("/ai/validate-model", payload);
    return response.data;
  },
  async modifyUml(payload: { instruction: string; classes: AiUmlResponse["classes"]; relationships: AiUmlResponse["relationships"] }) {
    const response = await apiClient.post<AiUmlResponse & { changes: string[] }>("/ai/uml/modify", payload);
    return response.data;
  },
  async knowledgeSearch(query: string) {
    const response = await apiClient.post<Array<{ topic: string; content: string; tags: string[] }>>("/ai/knowledge/search", {
      query,
      limit: 3
    });
    return response.data;
  },
  async evaluation() {
    const response = await apiClient.get<{
      dataset_size: number;
      class_precision: number;
      relationship_precision: number;
      average_score: number;
      offline: boolean;
    }>("/ai/evaluation/offline");
    return response.data;
  }
};
