import { clienteApi } from "../../../core/api/cliente";
import type {
  ModeloDiagrama,
  AtributoUML,
  ClaseUML,
  DetalleClaseUML,
  DiagramaUML,
  MetodoUML,
  EspecificacionMetodo,
  EnvolturaEspecificacionMetodo,
  PropuestaEspecificacionMetodo,
  PreparacionMetodo,
  RelacionUML,
  ValidacionUML,
  ElementoVisualUML
} from "../types/uml";
import type { RespuestaUMLIA } from "./servicioIA";

function normalizarTipoRelacion(type: string) {
  const normalized = type.toLowerCase();
  if (normalized === "generalization") {
    return "inheritance";
  }
  if (["association", "inheritance", "implementation", "dependency", "aggregation", "composition"].includes(normalized)) {
    return normalized;
  }
  return "association";
}

function posicionParaClase(index: number, total: number, className: string, associationClassNames: Set<string>) {
  if (associationClassNames.has(className.toLowerCase())) {
    return { position_x: 360, position_y: 350 };
  }
  if (total === 3 && associationClassNames.size > 0) {
    return {
      position_x: index === 0 ? 80 : 620,
      position_y: 100
    };
  }
  if (total <= 3) {
    return { position_x: 80 + index * 330, position_y: 110 };
  }
  return {
    position_x: 80 + (index % 3) * 330,
    position_y: 100 + Math.floor(index / 3) * 240
  };
}

export const servicioUML = {
  async crearDiagrama(payload: { project_id: string; name: string; description?: string }) {
    const response = await clienteApi.post<DiagramaUML>("/uml/diagrams", {
      ...payload,
      metadata_json: {}
    });
    return response.data;
  },
  async listarDiagramas(projectId: string) {
    const response = await clienteApi.get<DiagramaUML[]>(`/uml/projects/${projectId}/diagrams`);
    return response.data;
  },
  async eliminarDiagrama(diagramId: string) {
    await clienteApi.delete(`/uml/diagrams/${diagramId}`);
  },
  async crearClase(
    diagramId: string,
    payload: { name: string; position_x: number; position_y: number; description?: string; stereotype?: string | null }
  ) {
    const response = await clienteApi.post<ClaseUML>(`/uml/diagrams/${diagramId}/classes`, {
      name: payload.name,
      position_x: payload.position_x,
      position_y: payload.position_y,
      description: payload.description,
      stereotype: payload.stereotype,
      visibility: "public",
      element_type: "class",
      metadata_json: { attributes: [], methods: [] }
    });
    return response.data;
  },
  async listarClases(diagramId: string) {
    const response = await clienteApi.get<ClaseUML[]>(`/uml/diagrams/${diagramId}/classes`);
    return response.data;
  },
  async obtenerModeloDiagrama(diagramId: string) {
    const response = await clienteApi.get<ModeloDiagrama>(`/uml/diagrams/${diagramId}/model`);
    return response.data;
  },
  async actualizarClase(classId: string, payload: Partial<Pick<ClaseUML, "name" | "visibility" | "description" | "stereotype">>) {
    const response = await clienteApi.patch<DetalleClaseUML>(`/uml/classes/${classId}`, payload);
    return response.data;
  },
  async eliminarClase(classId: string) {
    await clienteApi.delete(`/uml/classes/${classId}`);
  },
  async moverElemento(diagramId: string, payload: { element_type: "class" | "relationship"; element_id: string; position_x: number; position_y: number }) {
    const response = await clienteApi.patch<ElementoVisualUML>(`/uml/diagrams/${diagramId}/visual-elements`, payload);
    return response.data;
  },
  async agregarAtributo(classId: string, payload: { name: string; data_type: string; visibility?: string | null; is_required?: boolean; order_index?: number }) {
    const response = await clienteApi.post<AtributoUML>(`/uml/classes/${classId}/attributes`, payload);
    return response.data;
  },
  async actualizarAtributo(attributeId: string, payload: Partial<Pick<AtributoUML, "name" | "data_type" | "visibility" | "initial_value" | "multiplicity" | "is_required" | "order_index" | "constraints">>) {
    const response = await clienteApi.patch<AtributoUML>(`/uml/attributes/${attributeId}`, payload);
    return response.data;
  },
  async eliminarAtributo(attributeId: string) {
    await clienteApi.delete(`/uml/attributes/${attributeId}`);
  },
  async agregarMetodo(classId: string, payload: { name: string; return_type?: string; visibility?: string | null; order_index?: number }) {
    const response = await clienteApi.post<MetodoUML>(`/uml/classes/${classId}/methods`, payload);
    return response.data;
  },
  async actualizarMetodo(methodId: string, payload: Partial<Pick<MetodoUML, "name" | "return_type" | "visibility" | "order_index" | "metadata_json">>) {
    const response = await clienteApi.patch<MetodoUML>(`/uml/methods/${methodId}`, payload);
    return response.data;
  },
  async eliminarMetodo(methodId: string) {
    await clienteApi.delete(`/uml/methods/${methodId}`);
  },
  async agregarParametro(methodId: string, payload: { name: string; data_type: string; default_value?: string | null; order_index?: number }) {
    return (await clienteApi.post<MetodoUML["parameters"][number]>(`/uml/methods/${methodId}/parameters`, payload)).data;
  },
  async actualizarParametro(parameterId: string, payload: Partial<MetodoUML["parameters"][number]>) {
    return (await clienteApi.patch<MetodoUML["parameters"][number]>(`/uml/parameters/${parameterId}`, payload)).data;
  },
  async eliminarParametro(parameterId: string) {
    await clienteApi.delete(`/uml/parameters/${parameterId}`);
  },
  async especificacionMetodo(methodId: string) {
    return (await clienteApi.get<EnvolturaEspecificacionMetodo>(`/uml/methods/${methodId}/specification`)).data;
  },
  async guardarEspecificacionMetodo(methodId: string, payload: Omit<EspecificacionMetodo, "id" | "method_id" | "revision" | "created_at" | "updated_at">, revision: number | null) {
    const headers = revision === null
      ? { "If-None-Match": "*" }
      : { "If-Match": `"revision-${revision}"` };
    return (await clienteApi.put<EspecificacionMetodo>(`/uml/methods/${methodId}/specification`, payload, { headers })).data;
  },
  async eliminarEspecificacionMetodo(methodId: string, revision: number) {
    await clienteApi.delete(`/uml/methods/${methodId}/specification`, {
      headers: { "If-Match": `"revision-${revision}"` }
    });
  },
  async validarEspecificacionMetodo(methodId: string, strict = false) {
    return (await clienteApi.post<PreparacionMetodo>(`/uml/methods/${methodId}/specification/validate`, undefined, { params: { strict } })).data;
  },
  async refinarEspecificacionMetodo(methodId: string, instruction: string, baseRevision: number) {
    return (await clienteApi.post<PropuestaEspecificacionMetodo>(`/uml/methods/${methodId}/specification/refine`, {
      instruction,
      base_revision: baseRevision,
      client_message_id: crypto.randomUUID()
    })).data;
  },
  async crearRelacion(
    diagramId: string,
    payload: {
      source_class_id: string;
      target_class_id: string;
      relationship_type: string;
      label?: string;
      source_cardinality?: string | null;
      target_cardinality?: string | null;
      metadata_json?: Record<string, unknown>;
    }
  ) {
    const response = await clienteApi.post<RelacionUML>(`/uml/diagrams/${diagramId}/relationships`, {
      ...payload,
      direction: "source_to_target",
      metadata_json: payload.metadata_json ?? {}
    });
    return response.data;
  },
  async actualizarRelacion(
    relationshipId: string,
    payload: Partial<
      Pick<RelacionUML, "relationship_type" | "label" | "source_cardinality" | "target_cardinality" | "direction" | "metadata_json">
    >
  ) {
    const response = await clienteApi.patch<RelacionUML>(`/uml/relationships/${relationshipId}`, payload);
    return response.data;
  },
  async eliminarRelacion(relationshipId: string) {
    await clienteApi.delete(`/uml/relationships/${relationshipId}`);
  },
  async validar(diagramId: string) {
    const response = await clienteApi.post<ValidacionUML>(`/uml/diagrams/${diagramId}/validate`);
    return response.data;
  },
  async generar(payload: { project_id: string; name: string; prompt: string; source_type: "text" | "voice" | "image" }) {
    const response = await clienteApi.post<DiagramaUML>("/uml/generate", payload);
    return response.data;
  },
  async crearDiagramaDesdeResultadoIA(payload: {
    project_id: string;
    name: string;
    description?: string;
    source_type: "text" | "voice" | "image";
    result: RespuestaUMLIA;
  }) {
    const associationClassNames = new Set(
      payload.result.relationships
        .map((relationship) => relationship.metadata_json?.association_class_name)
        .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
        .map((value) => value.toLowerCase())
    );
    const diagram = await this.crearDiagrama({
      project_id: payload.project_id,
      name: payload.name,
      description: payload.description
    });
    const classByName = new Map<string, ClaseUML>();
    for (const [index, aiClass] of payload.result.classes.entries()) {
      const createdClass = await this.crearClase(diagram.id, {
        name: aiClass.name,
        stereotype: aiClass.stereotype,
        ...posicionParaClase(index, payload.result.classes.length, aiClass.name, associationClassNames)
      });
      classByName.set(aiClass.name.toLowerCase(), createdClass);
      for (const [attributeIndex, attribute] of (aiClass.attributes ?? []).entries()) {
        await this.agregarAtributo(createdClass.id, {
          name: attribute.name,
          data_type: attribute.data_type || "String",
          visibility: attribute.visibility ?? "private",
          is_required: Boolean(attribute.is_required),
          order_index: attributeIndex
        });
      }
      for (const [methodIndex, method] of (aiClass.methods ?? []).entries()) {
        await this.agregarMetodo(createdClass.id, {
          name: method.name,
          return_type: method.return_type || "void",
          visibility: method.visibility ?? "public",
          order_index: methodIndex
        });
      }
    }
    for (const relationship of payload.result.relationships) {
      const source = classByName.get(relationship.source.toLowerCase());
      const target = classByName.get(relationship.target.toLowerCase());
      if (!source || !target) {
        continue;
      }
      const metadata = { ...(relationship.metadata_json ?? {}) };
      const associationClassName = metadata.association_class_name;
      if (typeof associationClassName === "string") {
        const associationClass = classByName.get(associationClassName.toLowerCase());
        if (associationClass) {
          metadata.association_class_id = associationClass.id;
        }
        delete metadata.association_class_name;
      }
      await this.crearRelacion(diagram.id, {
        source_class_id: source.id,
        target_class_id: target.id,
        relationship_type: normalizarTipoRelacion(relationship.relationship_type),
        label: relationship.label ?? undefined,
        source_cardinality: relationship.source_cardinality ?? null,
        target_cardinality: relationship.target_cardinality ?? null,
        metadata_json: metadata
      });
    }
    return diagram;
  },
  async aplicarModificacionIAAlDiagrama(payload: {
    diagramId: string;
    classes: DetalleClaseUML[];
    relationships: RelacionUML[];
    result: RespuestaUMLIA;
  }) {
    const associationClassNames = new Set(
      payload.result.relationships
        .map((relationship) => relationship.metadata_json?.association_class_name)
        .filter((value): value is string => typeof value === "string" && value.trim().length > 0)
        .map((value) => value.toLowerCase())
    );
    const classByName = new Map<string, ClaseUML | DetalleClaseUML>(
      payload.classes.map((umlClass) => [umlClass.name.toLowerCase(), umlClass])
    );

    for (const [index, aiClass] of payload.result.classes.entries()) {
      let targetClass = classByName.get(aiClass.name.toLowerCase());
      if (!targetClass) {
        targetClass = await this.crearClase(payload.diagramId, {
          name: aiClass.name,
          stereotype: aiClass.stereotype,
          ...posicionParaClase(payload.classes.length + index, payload.classes.length + payload.result.classes.length, aiClass.name, associationClassNames)
        });
        classByName.set(aiClass.name.toLowerCase(), targetClass);
      }

      const existingAttributes =
        "attributes" in targetClass ? new Set(targetClass.attributes.map((attribute) => attribute.name.toLowerCase())) : new Set<string>();
      for (const [attributeIndex, attribute] of (aiClass.attributes ?? []).entries()) {
        if (existingAttributes.has(attribute.name.toLowerCase())) {
          continue;
        }
        await this.agregarAtributo(targetClass.id, {
          name: attribute.name,
          data_type: attribute.data_type || "String",
          visibility: attribute.visibility ?? "private",
          is_required: Boolean(attribute.is_required),
          order_index: existingAttributes.size + attributeIndex
        });
        existingAttributes.add(attribute.name.toLowerCase());
      }

      const existingMethods =
        "methods" in targetClass ? new Set(targetClass.methods.map((method) => method.name.toLowerCase())) : new Set<string>();
      for (const [methodIndex, method] of (aiClass.methods ?? []).entries()) {
        if (existingMethods.has(method.name.toLowerCase())) {
          continue;
        }
        await this.agregarMetodo(targetClass.id, {
          name: method.name,
          return_type: method.return_type || "void",
          visibility: method.visibility ?? "public",
          order_index: existingMethods.size + methodIndex
        });
        existingMethods.add(method.name.toLowerCase());
      }
    }

    for (const relationship of payload.result.relationships) {
      const source = classByName.get(relationship.source.toLowerCase());
      const target = classByName.get(relationship.target.toLowerCase());
      if (!source || !target) {
        continue;
      }
      const metadata = { ...(relationship.metadata_json ?? {}) };
      const associationClassName = metadata.association_class_name;
      if (typeof associationClassName === "string") {
        const associationClass = classByName.get(associationClassName.toLowerCase());
        if (associationClass) {
          metadata.association_class_id = associationClass.id;
        }
        delete metadata.association_class_name;
      }

      const existingRelationship = payload.relationships.find((item) => {
        const sameDirection = item.source_class_id === source.id && item.target_class_id === target.id;
        const reverseDirection = item.source_class_id === target.id && item.target_class_id === source.id;
        return (sameDirection || reverseDirection) && normalizarTipoRelacion(item.relationship_type) === normalizarTipoRelacion(relationship.relationship_type);
      });

      if (existingRelationship) {
        await this.actualizarRelacion(existingRelationship.id, {
          relationship_type: normalizarTipoRelacion(relationship.relationship_type),
          label: relationship.label ?? existingRelationship.label,
          source_cardinality: relationship.source_cardinality ?? existingRelationship.source_cardinality,
          target_cardinality: relationship.target_cardinality ?? existingRelationship.target_cardinality,
          metadata_json: { ...existingRelationship.metadata_json, ...metadata }
        });
        continue;
      }

      await this.crearRelacion(payload.diagramId, {
        source_class_id: source.id,
        target_class_id: target.id,
        relationship_type: normalizarTipoRelacion(relationship.relationship_type),
        label: relationship.label ?? undefined,
        source_cardinality: relationship.source_cardinality ?? null,
        target_cardinality: relationship.target_cardinality ?? null,
        metadata_json: metadata
      });
    }
  },
  async importarXmi(payload: { project_id: string; name: string; content: string; file_name: string }) {
    const response = await clienteApi.post<DiagramaUML>("/uml/xmi/import", payload);
    return response.data;
  },
  async importarXmiAlDiagrama(diagramId: string, payload: { project_id: string; name: string; content: string; file_name: string }) {
    const response = await clienteApi.post<DiagramaUML>(`/uml/diagrams/${diagramId}/xmi/import`, payload);
    return response.data;
  },
  async exportarXmi(diagramId: string) {
    const response = await clienteApi.get<{ diagram_id: string; file_name: string; content: string }>(`/uml/diagrams/${diagramId}/xmi`);
    return response.data;
  }
};
