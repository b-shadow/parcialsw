import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Image, Mic, Plus, Save, Trash2, X } from "lucide-react";

import { createProjectSocket, sendProjectEvent } from "../../../core/websocket/projectSocket";
import { useThemeStore } from "../../../core/theme/themeStore";
import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { cn } from "../../../shared/utils/cn";
import { JointUmlCanvas } from "../components/JointUmlCanvas";
import { UmlToolbar } from "../components/UmlToolbar";
import { aiService } from "../services/aiService";
import { umlService } from "../services/umlService";
import { useUmlStore } from "../store/umlStore";
import type { UmlAttribute, UmlMethod } from "../types/uml";

type UmlTool = "select" | "class" | "association" | "inheritance" | "associationClass";

const relationshipOptions = [
  { value: "association", label: "Asociacion", line: "Linea continua" },
  { value: "inheritance", label: "Herencia", line: "Generalizacion" },
  { value: "implementation", label: "Implementacion", line: "Realizacion" },
  { value: "dependency", label: "Dependencia", line: "Linea punteada" },
  { value: "aggregation", label: "Agregacion", line: "Todo-parte debil" },
  { value: "composition", label: "Composicion", line: "Todo-parte fuerte" }
];

const visibilityOptions = [
  { value: "public", label: "Publico", symbol: "+" },
  { value: "private", label: "Privado", symbol: "-" }
];

const springDataTypes = [
  "String",
  "Integer",
  "Long",
  "Double",
  "BigDecimal",
  "Boolean",
  "Character",
  "LocalDate",
  "LocalDateTime",
  "UUID"
];

function visibilitySymbol(visibility: string) {
  return visibilityOptions.find((option) => option.value === visibility)?.symbol ?? "+";
}

type AiUmlResult = Awaited<ReturnType<typeof aiService.textToUml>>;

type BrowserSpeechRecognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: { results: ArrayLike<{ 0: { transcript: string } }> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start: () => void;
};

type BrowserFileSystemFileHandle = {
  getFile: () => Promise<File>;
};

type BrowserWindowWithFilePicker = Window & {
  showOpenFilePicker?: (options?: {
    multiple?: boolean;
    types?: Array<{
      description: string;
      accept: Record<string, string[]>;
    }>;
  }) => Promise<BrowserFileSystemFileHandle[]>;
};

function fileToBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function fileToText(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

function promptFromAiResult(result: AiUmlResult, fallback: string) {
  const classNames = result.classes.map((umlClass) => umlClass.name).filter(Boolean);
  const relations = result.relationships
    .map((relationship) => `${relationship.source} ${relationship.relationship_type} ${relationship.target}`)
    .join(", ");
  return [
    fallback,
    classNames.length > 0 ? `Clases: ${classNames.join(", ")}` : "",
    relations ? `Relaciones: ${relations}` : ""
  ]
    .filter(Boolean)
    .join(". ");
}

export function UmlEditorPage() {
  const { projectId = "", diagramId = "" } = useParams();
  const socketRef = useRef<WebSocket | null>(null);
  const isDark = useThemeStore((state) => state.mode === "dark");
  const classes = useUmlStore((state) => state.classes);
  const relationships = useUmlStore((state) => state.relationships);
  const validation = useUmlStore((state) => state.validation);
  const selectedClassId = useUmlStore((state) => state.selectedClassId);
  const setClasses = useUmlStore((state) => state.setClasses);
  const addClass = useUmlStore((state) => state.addClass);
  const updateClass = useUmlStore((state) => state.updateClass);
  const removeClass = useUmlStore((state) => state.removeClass);
  const addRelationship = useUmlStore((state) => state.addRelationship);
  const updateRelationship = useUmlStore((state) => state.updateRelationship);
  const removeRelationship = useUmlStore((state) => state.removeRelationship);
  const setRelationships = useUmlStore((state) => state.setRelationships);
  const setValidation = useUmlStore((state) => state.setValidation);
  const setSelectedClassId = useUmlStore((state) => state.setSelectedClassId);
  const [className, setClassName] = useState("Cliente");
  const [sourcePrompt, setSourcePrompt] = useState("Crear sistema de biblioteca con libros, usuarios y prestamos");
  const [aiObservation, setAiObservation] = useState("Motor IA local listo.");
  const [xmiContent, setXmiContent] = useState("");
  const [attributeName, setAttributeName] = useState("nombre");
  const [attributeType, setAttributeType] = useState("String");
  const [methodName, setMethodName] = useState("calcular");
  const [methodReturnType, setMethodReturnType] = useState("void");
  const [relationshipSourceId, setRelationshipSourceId] = useState("");
  const [relationshipTargetId, setRelationshipTargetId] = useState("");
  const [relationshipType, setRelationshipType] = useState("association");
  const [relationshipLabel, setRelationshipLabel] = useState("usa");
  const [sourceMultiplicity, setSourceMultiplicity] = useState("1");
  const [targetMultiplicity, setTargetMultiplicity] = useState("0..*");
  const [activeTool, setActiveTool] = useState<UmlTool>("select");
  const [pendingSourceId, setPendingSourceId] = useState("");
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [isCreatingClass, setIsCreatingClass] = useState(false);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("desconectado");
  const [canvasRevision, setCanvasRevision] = useState(0);
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const xmiInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    refreshDiagramModel();
  }, [diagramId, setClasses, setRelationships]);

  async function refreshDiagramModel() {
    try {
      const model = await umlService.getDiagramModel(diagramId);
      setClasses(model.classes);
      setRelationships(model.relationships);
      return model;
    } catch {
      setClasses([]);
      setRelationships([]);
      return null;
    }
  }

  useEffect(() => {
    if (!projectId) {
      return;
    }
    const socket = createProjectSocket(projectId);
    socketRef.current = socket;
    socket.onopen = () => setConnectionStatus("conectado");
    socket.onclose = () => setConnectionStatus("desconectado");
    socket.onerror = () => setConnectionStatus("error");
    socket.onmessage = () => undefined;
    return () => socket.close();
  }, [projectId]);

  const selectedClass = classes.find((umlClass) => umlClass.id === selectedClassId) ?? null;
  const selectedRelationship = relationships.find((relationship) => relationship.id === selectedRelationshipId) ?? null;

  useEffect(() => {
    if (classes.length === 0) {
      setRelationshipSourceId("");
      setRelationshipTargetId("");
      return;
    }
    setRelationshipSourceId((current) => (classes.some((umlClass) => umlClass.id === current) ? current : classes[0].id));
    setRelationshipTargetId((current) => {
      if (classes.some((umlClass) => umlClass.id === current) && current !== relationshipSourceId) {
        return current;
      }
      return classes.find((umlClass) => umlClass.id !== relationshipSourceId)?.id ?? classes[0].id;
    });
  }, [classes, relationshipSourceId]);

  useEffect(() => {
    if (selectedClass) {
      setClassName(selectedClass.name);
    }
  }, [selectedClass?.id, selectedClass?.name]);

  useEffect(() => {
    if (selectedRelationship) {
      setRelationshipLabel(selectedRelationship.label ?? "");
      setSourceMultiplicity(selectedRelationship.source_cardinality ?? "");
      setTargetMultiplicity(selectedRelationship.target_cardinality ?? "");
      setRelationshipType(selectedRelationship.relationship_type);
      setRelationshipSourceId(selectedRelationship.source_class_id);
      setRelationshipTargetId(selectedRelationship.target_class_id);
    }
  }, [selectedRelationship]);

  useEffect(() => {
    function handleDeleteKey(event: KeyboardEvent) {
      if (event.key !== "Delete") {
        return;
      }
      const target = event.target as HTMLElement | null;
      if (
        target?.tagName === "INPUT" ||
        target?.tagName === "TEXTAREA" ||
        target?.tagName === "SELECT" ||
        target?.isContentEditable
      ) {
        return;
      }
      if (selectedClassId) {
        event.preventDefault();
        void deleteSelectedClass();
        return;
      }
      if (selectedRelationshipId) {
        event.preventDefault();
        void deleteSelectedRelationship();
      }
    }

    window.addEventListener("keydown", handleDeleteKey);
    return () => window.removeEventListener("keydown", handleDeleteKey);
  }, [selectedClassId, selectedRelationshipId, selectedClass, selectedRelationship]);

  async function handleAddClass() {
    if (isCreatingClass) {
      return;
    }
    const position = {
      x: 90,
      y: 90
    };
    setIsCreatingClass(true);
    try {
      const created = await umlService.createClass(diagramId, {
        name: `Clase${classes.length + 1}`,
        position_x: position.x,
        position_y: position.y
      });
      addClass({
        ...created,
        attributes: [],
        methods: [],
        visual: {
          id: `local-${created.id}`,
          diagram_id: diagramId,
          element_type: "class",
          element_id: created.id,
          position_x: position.x,
          position_y: position.y,
          width: null,
          height: null,
          style: {}
        }
      });
      setSelectedClassId(created.id);
      setSelectedRelationshipId(null);
      setActiveTool("select");
      setClassName(created.name);
      sendProjectEvent(socketRef.current, { action: "CREATE_CLASS", class_id: created.id });
    } catch {
      setAiObservation("No se pudo crear la clase. Revise la sesion o la conexion con el backend.");
    } finally {
      setIsCreatingClass(false);
    }
  }

  async function handleValidate() {
    await refreshDiagramModel();
    setValidation(await umlService.validate(diagramId));
    setShowValidationModal(true);
  }

  function renameClassInline(classId: string, name: string) {
    const umlClass = useUmlStore.getState().classes.find((item) => item.id === classId);
    if (!umlClass) {
      return;
    }
    updateClass({ ...umlClass, name });
    if (selectedClassId === classId) {
      setClassName(name);
    }
    if (name.trim().length > 0) {
      void umlService.updateClass(classId, { name: name.trim() }).then((updated) => {
        const current = useUmlStore.getState().classes.find((item) => item.id === classId);
        if (current) {
          updateClass({ ...current, ...updated });
        }
      });
    }
  }

  async function handleCreateRelationship() {
    if (classes.length < 2 || !relationshipSourceId || !relationshipTargetId || relationshipSourceId === relationshipTargetId) {
      return;
    }
    const created = await umlService.createRelationship(diagramId, {
      source_class_id: relationshipSourceId,
      target_class_id: relationshipTargetId,
      relationship_type: relationshipType,
      label: relationshipLabel.trim() || relationshipType,
      source_cardinality: sourceMultiplicity.trim() || null,
      target_cardinality: targetMultiplicity.trim() || null
    });
    addRelationship(created);
    sendProjectEvent(socketRef.current, { action: "CREATE_RELATIONSHIP", relationship_id: created.id });
  }

  async function createRelationshipBetween(sourceId: string, targetId: string, tool: UmlTool) {
    if (sourceId === targetId) {
      return;
    }
    if (tool === "associationClass") {
      const sourceClass = classes.find((item) => item.id === sourceId);
      const targetClass = classes.find((item) => item.id === targetId);
      const positionX = ((sourceClass?.visual?.position_x ?? 160) + (targetClass?.visual?.position_x ?? 520)) / 2;
      const positionY = ((sourceClass?.visual?.position_y ?? 120) + (targetClass?.visual?.position_y ?? 120)) / 2 + 180;
      const associationClass = await umlService.createClass(diagramId, {
        name: `${sourceClass?.name ?? "Origen"}${targetClass?.name ?? "Destino"}`,
        position_x: positionX,
        position_y: positionY
      });
      const generatedAttribute = await umlService.addAttribute(associationClass.id, {
        name: `id${sourceClass?.name ?? "Origen"}`,
        data_type: "Long"
      });
      addClass({
        ...associationClass,
        attributes: [generatedAttribute],
        methods: [],
        visual: {
          id: `local-${associationClass.id}`,
          diagram_id: diagramId,
          element_type: "class",
          element_id: associationClass.id,
          position_x: positionX,
          position_y: positionY,
          width: null,
          height: null,
          style: {}
        }
      });
      const association = await umlService.createRelationship(diagramId, {
        source_class_id: sourceId,
        target_class_id: targetId,
        relationship_type: "association",
        label: relationshipLabel.trim() || "",
        source_cardinality: sourceMultiplicity.trim() || null,
        target_cardinality: targetMultiplicity.trim() || null,
        metadata_json: { association_class_id: associationClass.id }
      });
      addRelationship(association);
      setSelectedClassId(associationClass.id);
      setSelectedRelationshipId(null);
      setPendingSourceId("");
      setActiveTool("select");
      return;
    }
    const type = tool === "inheritance" ? "inheritance" : "association";
    const created = await umlService.createRelationship(diagramId, {
      source_class_id: sourceId,
      target_class_id: targetId,
      relationship_type: type,
      label: type === "inheritance" ? "generaliza" : relationshipLabel.trim() || "asocia",
      source_cardinality: type === "association" ? sourceMultiplicity.trim() || null : null,
      target_cardinality: type === "association" ? targetMultiplicity.trim() || null : null
    });
    addRelationship(created);
    setSelectedRelationshipId(created.id);
    setSelectedClassId(null);
    setPendingSourceId("");
    setActiveTool("select");
    sendProjectEvent(socketRef.current, { action: "CREATE_RELATIONSHIP", relationship_id: created.id });
  }

  const handleClassClick = useCallback(
    (classId: string) => {
      if (activeTool === "association" || activeTool === "inheritance" || activeTool === "associationClass") {
        if (!pendingSourceId) {
          setPendingSourceId(classId);
          setSelectedClassId(classId);
          setSelectedRelationshipId(null);
          return;
        }
        void createRelationshipBetween(pendingSourceId, classId, activeTool);
        setPendingSourceId("");
        return;
      }
      setSelectedClassId(classId);
      setSelectedRelationshipId(null);
      setRelationshipSourceId(classId);
      setRelationshipTargetId((current) => (current && current !== classId ? current : classes.find((umlClass) => umlClass.id !== classId)?.id ?? ""));
    },
    [activeTool, classes, pendingSourceId, setSelectedClassId]
  );

  const handleRelationshipClick = useCallback((relationshipId: string) => {
    setSelectedRelationshipId(relationshipId);
    setSelectedClassId(null);
    setPendingSourceId("");
  }, [setSelectedClassId]);

  const handleClassMove = useCallback(
    (classId: string, position: { x: number; y: number }) => {
      const umlClass = classes.find((item) => item.id === classId);
      if (umlClass) {
        updateClass({
          ...umlClass,
          visual: {
            id: umlClass.visual?.id ?? `local-${classId}`,
            diagram_id: diagramId,
            element_type: "class",
            element_id: classId,
            position_x: position.x,
            position_y: position.y,
            width: umlClass.visual?.width ?? null,
            height: umlClass.visual?.height ?? null,
            style: umlClass.visual?.style ?? {}
          }
        });
      }
      void umlService.moveElement(diagramId, {
        element_type: "class",
        element_id: classId,
        position_x: position.x,
        position_y: position.y
      }).then((visual) => {
        const movedClass = useUmlStore.getState().classes.find((item) => item.id === classId);
        if (movedClass) {
          updateClass({ ...movedClass, visual });
        }
      });
      sendProjectEvent(socketRef.current, { action: "MOVE_ELEMENT", class_id: classId, position });
    },
    [classes, diagramId, updateClass]
  );

  async function saveSelectedClass() {
    if (!selectedClass) {
      return;
    }
    const updated = await umlService.updateClass(selectedClass.id, { name: className });
    updateClass({ ...selectedClass, ...updated });
    sendProjectEvent(socketRef.current, { action: "UPDATE_CLASS", class_id: updated.id });
  }

  async function deleteSelectedClass() {
    if (!selectedClass) {
      return;
    }
    const relatedRelationshipIds = relationships
      .filter(
        (relationship) =>
          relationship.source_class_id === selectedClass.id ||
          relationship.target_class_id === selectedClass.id ||
          relationship.metadata_json?.association_class_id === selectedClass.id
      )
      .map((relationship) => relationship.id);
    await umlService.deleteClass(selectedClass.id);
    relatedRelationshipIds.forEach(removeRelationship);
    removeClass(selectedClass.id);
    setSelectedClassId(null);
    setSelectedRelationshipId(null);
    await refreshDiagramModel();
    sendProjectEvent(socketRef.current, { action: "DELETE_CLASS", class_id: selectedClass.id });
  }

  async function saveSelectedRelationship() {
    if (!selectedRelationship) {
      return;
    }
    const updated = await umlService.updateRelationship(selectedRelationship.id, {
      label: relationshipLabel.trim() || null,
      source_cardinality: sourceMultiplicity.trim() || null,
      target_cardinality: targetMultiplicity.trim() || null,
      relationship_type: relationshipType
    });
    updateRelationship(updated);
    sendProjectEvent(socketRef.current, { action: "UPDATE_RELATIONSHIP", relationship_id: updated.id });
  }

  async function deleteSelectedRelationship() {
    if (!selectedRelationship) {
      return;
    }
    await umlService.deleteRelationship(selectedRelationship.id);
    removeRelationship(selectedRelationship.id);
    setSelectedRelationshipId(null);
    await refreshDiagramModel();
    sendProjectEvent(socketRef.current, { action: "DELETE_RELATIONSHIP", relationship_id: selectedRelationship.id });
  }

  async function addAttributeToSelectedClass() {
    if (!selectedClass || attributeName.trim().length === 0 || attributeType.trim().length === 0) {
      return;
    }
    const created = await umlService.addAttribute(selectedClass.id, {
      name: attributeName.trim(),
      data_type: attributeType.trim()
    });
    updateClass({ ...selectedClass, attributes: [...selectedClass.attributes, created] });
    setAttributeName("");
    sendProjectEvent(socketRef.current, { action: "CREATE_ATTRIBUTE", attribute_id: created.id });
  }

  async function saveAttribute(attributeId: string) {
    if (!selectedClass) {
      return;
    }
    const attribute = selectedClass.attributes.find((item) => item.id === attributeId);
    if (!attribute) {
      return;
    }
    const updated = await umlService.updateAttribute(attributeId, {
      name: attribute.name,
      data_type: attribute.data_type,
      visibility: attribute.visibility,
      is_required: attribute.is_required,
      initial_value: attribute.initial_value,
      multiplicity: attribute.multiplicity,
      order_index: attribute.order_index,
      constraints: attribute.constraints
    });
    updateClass({
      ...selectedClass,
      attributes: selectedClass.attributes.map((item) => (item.id === attributeId ? updated : item))
    });
    sendProjectEvent(socketRef.current, { action: "UPDATE_ATTRIBUTE", attribute_id: attributeId });
  }

  async function deleteAttribute(attributeId: string) {
    if (!selectedClass) {
      return;
    }
    await umlService.deleteAttribute(attributeId);
    updateClass({ ...selectedClass, attributes: selectedClass.attributes.filter((item) => item.id !== attributeId) });
    sendProjectEvent(socketRef.current, { action: "DELETE_ATTRIBUTE", attribute_id: attributeId });
  }

  function updateAttributeDraft(attributeId: string, patch: Partial<UmlAttribute>) {
    if (!selectedClass) {
      return;
    }
    updateClass({
      ...selectedClass,
      attributes: selectedClass.attributes.map((item) => (item.id === attributeId ? { ...item, ...patch } : item))
    });
  }

  async function addMethodToSelectedClass() {
    if (!selectedClass || methodName.trim().length === 0) {
      return;
    }
    const created = await umlService.addMethod(selectedClass.id, {
      name: methodName.trim(),
      return_type: methodReturnType.trim() || "void"
    });
    updateClass({ ...selectedClass, methods: [...selectedClass.methods, created] });
    setMethodName("");
    sendProjectEvent(socketRef.current, { action: "CREATE_METHOD", method_id: created.id });
  }

  async function saveMethod(methodId: string) {
    if (!selectedClass) {
      return;
    }
    const method = selectedClass.methods.find((item) => item.id === methodId);
    if (!method) {
      return;
    }
    const updated = await umlService.updateMethod(methodId, {
      name: method.name,
      return_type: method.return_type,
      visibility: method.visibility,
      order_index: method.order_index,
      metadata_json: method.metadata_json
    });
    updateClass({
      ...selectedClass,
      methods: selectedClass.methods.map((item) => (item.id === methodId ? updated : item))
    });
    sendProjectEvent(socketRef.current, { action: "UPDATE_METHOD", method_id: methodId });
  }

  async function deleteMethod(methodId: string) {
    if (!selectedClass) {
      return;
    }
    await umlService.deleteMethod(methodId);
    updateClass({ ...selectedClass, methods: selectedClass.methods.filter((item) => item.id !== methodId) });
    sendProjectEvent(socketRef.current, { action: "DELETE_METHOD", method_id: methodId });
  }

  function updateMethodDraft(methodId: string, patch: Partial<UmlMethod>) {
    if (!selectedClass) {
      return;
    }
    updateClass({
      ...selectedClass,
      methods: selectedClass.methods.map((item) => (item.id === methodId ? { ...item, ...patch } : item))
    });
  }

  async function generateFromSource(sourceType: "text" | "voice" | "image", file?: File, promptOverride?: string) {
    const basePrompt = promptOverride?.trim() || sourcePrompt.trim() || "Modelo UML generado por IA local";
    const aiResult =
      sourceType === "text"
        ? await aiService.textToUml(basePrompt)
        : sourceType === "voice"
          ? await aiService.voiceToUml({ transcript: basePrompt })
          : await aiService.imageToUml({
              description: basePrompt,
              image_base64: file ? await fileToBase64(file) : undefined,
              file_name: file?.name
            });
    setAiObservation(
      `${aiResult.engine} confianza ${Math.round(aiResult.confidence * 100)}%: ${aiResult.classes
        .map((umlClass) => umlClass.name)
        .join(", ")}`
    );
    const generated = await umlService.generate({
      project_id: projectId,
      name: `UML generado ${sourceType}`,
      prompt: promptFromAiResult(aiResult, basePrompt),
      source_type: sourceType
    });
    window.location.href = `/proyectos/${projectId}/uml/${generated.id}`;
  }

  async function importXmi(content = xmiContent, fileName = "modelo-importado.xml") {
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      setAiObservation("No se importo nada: el archivo XML esta vacio.");
      return;
    }
    setAiObservation(`Importando ${fileName}...`);
    try {
      await umlService.importXmiIntoDiagram(diagramId, {
        project_id: projectId,
        name: fileName.replace(/\.[^.]+$/, "") || "Modelo importado XML",
        file_name: fileName,
        content: trimmedContent
      });
      setSelectedClassId(null);
      setSelectedRelationshipId(null);
      setPendingSourceId("");
      setActiveTool("select");
      const model = await refreshDiagramModel();
      setCanvasRevision((current) => current + 1);
      setXmiContent("");
      if (!model || model.classes.length === 0) {
        setAiObservation(`XML importado, pero el modelo quedo sin clases dibujables. Revise el formato de ${fileName}.`);
        return;
      }
      setAiObservation(`XML importado correctamente: ${fileName}. ${model.classes.length} clases y ${model.relationships.length} relaciones dibujadas.`);
    } catch (error) {
      const detail =
        error instanceof Error && error.message.trim().length > 0
          ? error.message
          : "El backend no acepto el XML o no pudo convertirlo al modelo UML.";
      setAiObservation(`No se pudo importar ${fileName}. ${detail}`);
      await refreshDiagramModel();
    }
  }

  async function handleImageSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) {
      await generateFromSource("image", file);
    }
  }

  async function handleXmiSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      setAiObservation("No se selecciono ningun archivo XML.");
      return;
    }
    setAiObservation(`Archivo seleccionado: ${file.name}. Leyendo ${file.size} bytes...`);
    try {
      await importXmi(await fileToText(file), file.name);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "No se pudo leer el archivo seleccionado.";
      setAiObservation(`No se pudo leer ${file.name}. ${detail}`);
    }
  }

  async function openXmiPicker() {
    setAiObservation("Seleccione un archivo XML exportado desde Enterprise Architect.");
    const browserWindow = window as BrowserWindowWithFilePicker;
    if (typeof browserWindow.showOpenFilePicker === "function") {
      try {
        const [handle] = await browserWindow.showOpenFilePicker({
          multiple: false,
          types: [
            {
              description: "Archivos XML / XMI",
              accept: {
                "application/xml": [".xml", ".xmi"],
                "text/xml": [".xml", ".xmi"],
                "text/plain": [".xml", ".xmi"],
              },
            },
          ],
        });
        if (!handle) {
          setAiObservation("Seleccion de archivo cancelada.");
          return;
        }
        const file = await handle.getFile();
        setAiObservation(`Archivo seleccionado: ${file.name}. Leyendo ${file.size} bytes...`);
        await importXmi(await fileToText(file), file.name);
        return;
      } catch (error) {
        const domError = error as { name?: string; message?: string };
        if (domError.name === "AbortError") {
          setAiObservation("Seleccion de archivo cancelada.");
          return;
        }
        setAiObservation(`No se pudo abrir o leer el archivo con el selector nativo. ${domError.message ?? ""}`.trim());
      }
    }
    if (!xmiInputRef.current) {
      setAiObservation("No se pudo abrir el selector de XML. Recargue la pagina e intente otra vez.");
      return;
    }
    xmiInputRef.current.value = "";
    xmiInputRef.current.click();
  }

  function startSpeechCapture() {
    const browserWindow = window as Window & {
      SpeechRecognition?: new () => BrowserSpeechRecognition;
      webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
    };
    const SpeechRecognition = browserWindow.SpeechRecognition ?? browserWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setAiObservation("El navegador no expone dictado. Escriba o pegue la transcripcion y use Voz.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ");
      setSourcePrompt(transcript);
      setAiObservation("Transcripcion capturada. Use Voz para generar el modelo UML.");
    };
    recognition.onerror = () => {
      setIsListening(false);
      setAiObservation("No se pudo capturar audio desde el navegador.");
    };
    recognition.onend = () => setIsListening(false);
    setIsListening(true);
    recognition.start();
  }

  function generateFromVoiceCapture() {
    const browserWindow = window as Window & {
      SpeechRecognition?: new () => BrowserSpeechRecognition;
      webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
    };
    const SpeechRecognition = browserWindow.SpeechRecognition ?? browserWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setAiObservation("El navegador no expone dictado. Escriba la descripcion y use Texto.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "es-ES";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ");
      setSourcePrompt(transcript);
      setAiObservation("Transcripcion capturada. Generando UML por voz.");
      void generateFromSource("voice", undefined, transcript);
    };
    recognition.onerror = () => {
      setIsListening(false);
      setAiObservation("No se pudo capturar audio desde el navegador.");
    };
    recognition.onend = () => setIsListening(false);
    setIsListening(true);
    recognition.start();
  }

  function exportXmi() {
    setAiObservation("Preparando XML para Enterprise Architect...");
    void umlService
      .exportXmi(diagramId)
      .then((xmi) => {
        const blob = new Blob([xmi.content], { type: "application/xml" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        const xmlFileName = xmi.file_name.replace(/\.[^.]+$/, "") + ".xml";
        anchor.href = url;
        anchor.download = xmlFileName;
        anchor.click();
        URL.revokeObjectURL(url);
        setAiObservation(`XML exportado correctamente: ${xmlFileName}.`);
      })
      .catch((error) => {
        const detail = error instanceof Error && error.message.trim().length > 0 ? error.message : "No se pudo generar el XML.";
        setAiObservation(`No se pudo exportar el XML. ${detail}`);
      });
  }

  function exportJsonSnapshot() {
    const blob = new Blob([JSON.stringify({ classes, relationships }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "modelo-uml.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className={cn("uml-editor-scope grid gap-4", isDark ? "uml-editor-dark" : "uml-editor-light")}>
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-semibold text-ink dark:text-white">Editor UML</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Canvas colaborativo de diagrama de clases.</p>
        </div>
        <StatusBadge tone={connectionStatus === "conectado" ? "success" : "warning"}>
          {connectionStatus}
        </StatusBadge>
      </div>

      <Panel className="overflow-hidden bg-white dark:border-slate-700 dark:bg-slate-950">
        <UmlToolbar
          onAddClass={handleAddClass}
          onValidate={handleValidate}
          onExport={exportXmi}
          onImport={openXmiPicker}
          onImage={() => imageInputRef.current?.click()}
        />
        <input ref={imageInputRef} className="hidden" type="file" accept="image/*" onChange={handleImageSelected} />
        <input
          ref={xmiInputRef}
          className="hidden"
          type="file"
          accept=".xml,.xmi,text/xml,application/xml,*/*"
          onChange={handleXmiSelected}
        />
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">
          {aiObservation}
        </div>
        <div className="grid min-h-[620px] xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="h-[620px] bg-slate-50 dark:bg-slate-900">
            <JointUmlCanvas
              activeTool={activeTool}
              classes={classes}
              isDark={isDark}
              key={`${diagramId}-${canvasRevision}`}
              onClassClick={handleClassClick}
              onClassMove={handleClassMove}
              onClassRename={renameClassInline}
              onRelationshipClick={handleRelationshipClick}
              pendingSourceId={pendingSourceId}
              relationships={relationships}
              selectedClassId={selectedClassId}
              selectedRelationshipId={selectedRelationshipId}
            />
          </div>
          <aside className="border-t border-slate-300 bg-[#f5f5f5] p-3 dark:border-slate-700 dark:bg-slate-950 xl:border-l xl:border-t-0">
            <div className="grid gap-3">
              <Panel className="overflow-hidden p-0 dark:border-slate-700 dark:bg-slate-900">
                <div className="border-b border-slate-300 bg-[#ececec] px-3 py-2 text-sm font-semibold text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-white">
                  Toolbox
                </div>
                <div className="grid gap-1 p-2">
                  <button
                    className={`flex h-9 items-center gap-2 rounded px-2 text-left text-sm ${activeTool === "select" ? "bg-teal-100 text-teal-900 dark:bg-teal-500/20 dark:text-teal-100" : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"}`}
                    onClick={() => {
                      setActiveTool("select");
                      setPendingSourceId("");
                    }}
                    type="button"
                  >
                    <span className="w-5 text-center text-lg">S</span> Select
                  </button>
                  <div className="mt-2 border-t border-slate-300 pt-2 text-xs font-semibold text-slate-600 dark:border-slate-700 dark:text-slate-400">
                    Class
                  </div>
                  <button
                    className="flex h-9 items-center gap-2 rounded px-2 text-left text-sm text-slate-700 hover:bg-slate-100 disabled:cursor-wait disabled:opacity-60 dark:text-slate-200 dark:hover:bg-slate-800"
                    disabled={isCreatingClass}
                    onClick={() => void handleAddClass()}
                    type="button"
                  >
                    <Plus size={16} aria-hidden="true" /> {isCreatingClass ? "Creando..." : "Class"}
                  </button>
                  <div className="mt-2 border-t border-slate-300 pt-2 text-xs font-semibold text-slate-600 dark:border-slate-700 dark:text-slate-400">
                    Class Relationships
                  </div>
                  {[
                    ["association", "Associate", "-"],
                    ["inheritance", "Generalize", "^"],
                    ["associationClass", "Association Class", "<>"],
                  ].map(([tool, label, glyph]) => (
                    <button
                      key={tool}
                      className={`flex h-9 items-center gap-2 rounded px-2 text-left text-sm ${activeTool === tool ? "bg-teal-100 text-teal-900 dark:bg-teal-500/20 dark:text-teal-100" : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"}`}
                      onClick={() => {
                        setActiveTool(tool as UmlTool);
                        setPendingSourceId("");
                      }}
                      type="button"
                    >
                      <span className="w-5 text-center text-sm font-semibold">{glyph}</span> {label}
                    </button>
                  ))}
                  <p className="mt-2 rounded bg-white px-2 py-2 text-xs text-slate-500 dark:bg-slate-950 dark:text-slate-400">
                    {pendingSourceId
                      ? "Origen seleccionado. Haga click en la clase destino."
                      : activeTool === "select"
                        ? "Arrastre clases o seleccione una linea."
                        : "Seleccione la clase origen y luego la clase destino."}
                  </p>
                </div>
              </Panel>

              {selectedRelationship && (
                <Panel className="grid gap-3 p-4 dark:border-slate-700 dark:bg-slate-900">
                  <h2 className="text-sm font-semibold text-ink dark:text-white">Relacion seleccionada</h2>
                  <Input label="Etiqueta" value={relationshipLabel} onChange={(event) => setRelationshipLabel(event.target.value)} />
                  <div className="grid grid-cols-2 gap-2">
                    <Input label="Origen" value={sourceMultiplicity} onChange={(event) => setSourceMultiplicity(event.target.value)} />
                    <Input label="Destino" value={targetMultiplicity} onChange={(event) => setTargetMultiplicity(event.target.value)} />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <Button icon={<Save size={16} aria-hidden="true" />} onClick={saveSelectedRelationship} variant="secondary">
                      Guardar
                    </Button>
                    <Button icon={<Trash2 size={16} aria-hidden="true" />} onClick={deleteSelectedRelationship} variant="danger">
                      Eliminar
                    </Button>
                  </div>
                </Panel>
              )}

              <Panel className="grid gap-3 p-4 dark:border-slate-700 dark:bg-slate-900">
                <h2 className="text-sm font-semibold text-ink dark:text-white">IA local preparada</h2>
                <textarea
                  className="min-h-24 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  value={sourcePrompt}
                  onChange={(event) => setSourcePrompt(event.target.value)}
                />
                <div className="grid grid-cols-3 gap-2">
                  <Button onClick={() => generateFromSource("text")} variant="secondary">Texto</Button>
                  <Button icon={<Mic size={16} aria-hidden="true" />} onClick={generateFromVoiceCapture} variant="secondary">
                    {isListening ? "Escuchando" : "Voz"}
                  </Button>
                  <Button icon={<Image size={16} aria-hidden="true" />} onClick={() => imageInputRef.current?.click()} variant="secondary">
                    Imagen a UML
                  </Button>
                </div>
                <p className="text-xs leading-5 text-slate-600 dark:text-slate-300">{aiObservation}</p>
              </Panel>
            </div>
          </aside>
        </div>

        <div className="border-t border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
          <Panel className="p-4 dark:border-slate-700 dark:bg-slate-950">
            <div className="flex flex-col justify-between gap-2 md:flex-row md:items-center">
              <div>
                <h2 className="text-lg font-semibold text-ink dark:text-white">Propiedades del elemento</h2>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {selectedClass ? `${selectedClass.name}: atributos y metodos editables` : "Seleccione una clase para editar atributos y metodos."}
                </p>
              </div>
              <div className="rounded-md border border-slate-200 px-3 py-2 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300">
                {relationships.length} relaciones en el diagrama
              </div>
            </div>

            <div className="mt-4 grid gap-4 xl:grid-cols-2">
              <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-700">
                <div className="border-b border-slate-200 bg-white px-3 py-2 font-semibold text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-white">
                  Atributos
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                      <tr>
                        <th className="w-24 px-3 py-2">Vis.</th>
                        <th className="px-3 py-2">Nombre</th>
                        <th className="px-3 py-2">Tipo</th>
                        <th className="w-36 px-3 py-2">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-950">
                      {selectedClass?.attributes.map((attribute) => (
                        <tr key={attribute.id}>
                          <td className="px-3 py-2">
                            <select
                              className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                              value={attribute.visibility}
                              onChange={(event) => updateAttributeDraft(attribute.id, { visibility: event.target.value })}
                            >
                              {visibilityOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.symbol} {option.label}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            <input
                              className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                              value={attribute.name}
                              onChange={(event) => updateAttributeDraft(attribute.id, { name: event.target.value })}
                            />
                          </td>
                          <td className="px-3 py-2">
                            <select
                              className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                              value={attribute.data_type}
                              onChange={(event) => updateAttributeDraft(attribute.id, { data_type: event.target.value })}
                            >
                              {springDataTypes.map((dataType) => (
                                <option key={dataType} value={dataType}>
                                  {dataType}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex gap-2">
                              <Button icon={<Save size={15} aria-hidden="true" />} onClick={() => saveAttribute(attribute.id)} variant="secondary">
                                Guardar
                              </Button>
                              <Button icon={<Trash2 size={15} aria-hidden="true" />} onClick={() => deleteAttribute(attribute.id)} variant="danger">
                                Eliminar
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td className="px-3 py-2 text-slate-500 dark:text-slate-400">{visibilitySymbol("private")} Privado</td>
                        <td className="px-3 py-2">
                          <input
                            className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                            disabled={!selectedClass}
                            placeholder="nombre"
                            value={attributeName}
                            onChange={(event) => setAttributeName(event.target.value)}
                          />
                        </td>
                        <td className="px-3 py-2">
                          <select
                            className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                            disabled={!selectedClass}
                            value={attributeType}
                            onChange={(event) => setAttributeType(event.target.value)}
                          >
                            {springDataTypes.map((dataType) => (
                              <option key={dataType} value={dataType}>
                                {dataType}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-3 py-2">
                          <Button disabled={!selectedClass} icon={<Plus size={15} aria-hidden="true" />} onClick={addAttributeToSelectedClass} variant="secondary">
                            Agregar
                          </Button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-700">
                <div className="border-b border-slate-200 bg-white px-3 py-2 font-semibold text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-white">
                  Metodos
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                      <tr>
                        <th className="w-24 px-3 py-2">Vis.</th>
                        <th className="px-3 py-2">Nombre</th>
                        <th className="px-3 py-2">Retorno</th>
                        <th className="w-36 px-3 py-2">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-950">
                      {selectedClass?.methods.map((method) => (
                        <tr key={method.id}>
                          <td className="px-3 py-2">
                            <select
                              className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                              value={method.visibility}
                              onChange={(event) => updateMethodDraft(method.id, { visibility: event.target.value })}
                            >
                              {visibilityOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.symbol} {option.label}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="px-3 py-2">
                            <input
                              className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                              value={method.name}
                              onChange={(event) => updateMethodDraft(method.id, { name: event.target.value })}
                            />
                          </td>
                          <td className="px-3 py-2">
                            <input
                              className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                              value={method.return_type ?? ""}
                              onChange={(event) => updateMethodDraft(method.id, { return_type: event.target.value })}
                            />
                          </td>
                          <td className="px-3 py-2">
                            <div className="flex gap-2">
                              <Button icon={<Save size={15} aria-hidden="true" />} onClick={() => saveMethod(method.id)} variant="secondary">
                                Guardar
                              </Button>
                              <Button icon={<Trash2 size={15} aria-hidden="true" />} onClick={() => deleteMethod(method.id)} variant="danger">
                                Eliminar
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td className="px-3 py-2 text-slate-500 dark:text-slate-400">{visibilitySymbol("public")} Publico</td>
                        <td className="px-3 py-2">
                          <input
                            className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                            disabled={!selectedClass}
                            placeholder="calcular"
                            value={methodName}
                            onChange={(event) => setMethodName(event.target.value)}
                          />
                        </td>
                        <td className="px-3 py-2">
                          <input
                            className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                            disabled={!selectedClass}
                            placeholder="void"
                            value={methodReturnType}
                            onChange={(event) => setMethodReturnType(event.target.value)}
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Button disabled={!selectedClass} icon={<Plus size={15} aria-hidden="true" />} onClick={addMethodToSelectedClass} variant="secondary">
                            Agregar
                          </Button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </Panel>
        </div>
      </Panel>

      {showValidationModal && validation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 px-4">
          <div className="w-full max-w-lg rounded-lg border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-950">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
              <div>
                <h2 className="text-lg font-semibold text-ink dark:text-white">Validacion UML</h2>
                <p className="text-sm text-slate-500 dark:text-slate-400">Resultado del analisis del diagrama.</p>
              </div>
              <button
                className="rounded-md p-2 text-slate-500 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                onClick={() => setShowValidationModal(false)}
                type="button"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="grid gap-4 px-5 py-4 text-sm">
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Errores</p>
                  <p className="text-xl font-semibold text-rose-600">{validation.errors.length}</p>
                </div>
                <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Advertencias</p>
                  <p className="text-xl font-semibold text-amber-600">{validation.warnings.length}</p>
                </div>
                <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700">
                  <p className="text-xs text-slate-500 dark:text-slate-400">Recomendaciones</p>
                  <p className="text-xl font-semibold text-accent">{validation.recommendations.length}</p>
                </div>
              </div>
              {[...validation.errors, ...validation.warnings, ...validation.recommendations].length > 0 ? (
                <ul className="max-h-56 list-disc overflow-auto pl-5 text-slate-700 dark:text-slate-200">
                  {validation.errors.map((item) => <li key={`error-${item}`}>{item}</li>)}
                  {validation.warnings.map((item) => <li key={`warning-${item}`}>{item}</li>)}
                  {validation.recommendations.map((item) => <li key={`recommendation-${item}`}>{item}</li>)}
                </ul>
              ) : (
                <p className="rounded-md bg-teal-50 px-3 py-2 text-slate-700 dark:bg-teal-500/10 dark:text-slate-200">
                  El diagrama no presenta observaciones.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

