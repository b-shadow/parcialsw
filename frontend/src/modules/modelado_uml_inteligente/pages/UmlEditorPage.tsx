import { ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  ArrowUpRight,
  Bot,
  ChevronDown,
  Diamond,
  Eye,
  GitBranch,
  History,
  Image,
  Link2,
  List,
  Mic,
  MousePointer2,
  Network,
  PencilRuler,
  Plus,
  Save,
  Send,
  Settings2,
  SlidersHorizontal,
  Square,
  Table2,
  Trash2,
  X
} from "lucide-react";

import {
  createProjectSocket,
  sendProjectEvent,
  type ProjectSocketEvent
} from "../../../core/websocket/projectSocket";
import { useThemeStore } from "../../../core/theme/themeStore";
import { Button } from "../../../shared/components/Button";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { cn } from "../../../shared/utils/cn";
import { JointUmlCanvas } from "../components/JointUmlCanvas";
import { MethodSpecificationEditor } from "../components/MethodSpecificationEditor";
import { UmlToolbar } from "../components/UmlToolbar";
import { ProjectAiAssistant } from "../../gestion_proyectos_colaboracion/components/ProjectAiAssistant";
import { ProjectHistoryPanel } from "../../gestion_proyectos_colaboracion/components/ProjectHistoryPanel";
import { aiService } from "../services/aiService";
import { ElementTypeSelect } from "../components/ElementTypeSelect";
import { umlService } from "../services/umlService";
import { useUmlStore } from "../store/umlStore";
import type { DiagramModel, UmlAttribute, UmlElementType, UmlMethod } from "../types/uml";

type UmlTool =
  | "select"
  | "class"
  | "association"
  | "inheritance"
  | "aggregation"
  | "composition"
  | "associationClass"
  | "dependency"
  | "realization";

const visibilityOptions = [
  { value: "public", label: "Publico", symbol: "+" },
  { value: "private", label: "Privado", symbol: "-" },
  { value: "protected", label: "Protegido", symbol: "#" },
  { value: "package", label: "Paquete", symbol: "~" }
];

const multiplicityOptions = ["", "0", "0..1", "1", "1..*", "0..*", "*"];

const relationshipTypeOptions = [
  { value: "association", label: "Association" },
  { value: "inheritance", label: "Generalization" },
  { value: "aggregation", label: "Aggregation" },
  { value: "composition", label: "Composition" },
  { value: "dependency", label: "Dependency" },
  { value: "realization", label: "Realization" }
] as const;

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

function createClientEventId() {
  if (typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  const bytes = new Uint8Array(16);
  if (typeof window.crypto.getRandomValues === "function") {
    window.crypto.getRandomValues(bytes);
  } else {
    for (let index = 0; index < bytes.length; index += 1) {
      bytes[index] = Math.floor(Math.random() * 256);
    }
  }
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hexadecimal = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  return `${hexadecimal.slice(0, 8)}-${hexadecimal.slice(8, 12)}-${hexadecimal.slice(12, 16)}-${hexadecimal.slice(16, 20)}-${hexadecimal.slice(20)}`;
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
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestedChatId = searchParams.get("chat");
  const socketRef = useRef<WebSocket | null>(null);
  const remoteRefreshTimerRef = useRef<number | null>(null);
  const pendingSocketEventsRef = useRef<Record<string, unknown>[]>([]);
  const lastEventSequenceRef = useRef<number | null>(null);
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
  const [sourcePrompt, setSourcePrompt] = useState("");
  const [aiObservation, setAiObservation] = useState("");
  const [xmiContent, setXmiContent] = useState("");
  const [attributeName, setAttributeName] = useState("nombre");
  const [attributeType, setAttributeType] = useState("String");
  const [methodName, setMethodName] = useState("calcular");
  const [methodReturnType, setMethodReturnType] = useState("void");
  const [relationshipType, setRelationshipType] = useState("association");
  const [relationshipLabel, setRelationshipLabel] = useState("usa");
  const [sourceMultiplicity, setSourceMultiplicity] = useState("1");
  const [targetMultiplicity, setTargetMultiplicity] = useState("0..*");
  const [activeTool, setActiveTool] = useState<UmlTool>("select");
  const [pendingSourceId, setPendingSourceId] = useState("");
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string | null>(null);
  const [isRelationshipModalOpen, setIsRelationshipModalOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isCreatingClass, setIsCreatingClass] = useState(false);
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("desconectado");
  const [canvasRevision, setCanvasRevision] = useState(0);
  const [specificationMethodId, setSpecificationMethodId] = useState<string | null>(null);
  const [rightPanelTab, setRightPanelTab] = useState<"editor" | "assistant" | "versions">(
    () => searchParams.get("panel") === "assistant" ? "assistant" : "editor"
  );
  const [elementsExpanded, setElementsExpanded] = useState(true);
  const [editingToolsExpanded, setEditingToolsExpanded] = useState(true);
  const [elementDetailsTab, setElementDetailsTab] = useState<"properties" | "relationships">("properties");
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const xmiInputRef = useRef<HTMLInputElement | null>(null);
  const attributeNameInputRef = useRef<HTMLInputElement | null>(null);
  const methodNameInputRef = useRef<HTMLInputElement | null>(null);

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
    let disposed = false;
    let retryCount = 0;
    let reconnectTimer: number | null = null;
    let lastServerMessageAt = Date.now();
    const heartbeatTimer = window.setInterval(() => {
      const activeSocket = socketRef.current;
      if (activeSocket?.readyState !== WebSocket.OPEN) return;
      if (Date.now() - lastServerMessageAt > 45000) {
        activeSocket.close(4000, "Servidor sin respuesta");
        return;
      }
      activeSocket.send(JSON.stringify({ type: "PING" }));
    }, 15000);

    function connect() {
      if (disposed) return;
      setConnectionStatus(retryCount > 0 ? "reconectando" : "conectando");
      const socket = createProjectSocket(projectId);
      socketRef.current = socket;
      socket.onopen = () => {
        const wasReconnecting = retryCount > 0;
        lastServerMessageAt = Date.now();
        retryCount = 0;
        setConnectionStatus("conectado");
        if (wasReconnecting) {
          void refreshDiagramModel().then(() => {
            setSelectedClassId(null);
            setSelectedRelationshipId(null);
            setCanvasRevision((current) => current + 1);
          });
        }
        pendingSocketEventsRef.current.forEach((payload) => sendProjectEvent(socket, payload));
      };
      socket.onclose = (event) => {
        if (socketRef.current === socket) socketRef.current = null;
        if (disposed) return;
        if (event.code === 1008) {
          setConnectionStatus("sin acceso");
          return;
        }
        setConnectionStatus("reconectando");
        const delay = Math.min(1000 * 2 ** retryCount, 10000);
        retryCount += 1;
        reconnectTimer = window.setTimeout(connect, delay);
      };
      socket.onerror = () => setConnectionStatus("error");
      socket.onmessage = (message) => {
        lastServerMessageAt = Date.now();
        let event: ProjectSocketEvent;
        try {
          event = JSON.parse(String(message.data)) as ProjectSocketEvent;
        } catch {
          return;
        }
        if (event.type === "EVENT_ACK" && event.client_event_id) {
          pendingSocketEventsRef.current = pendingSocketEventsRef.current.filter(
            (pending) => pending.client_event_id !== event.client_event_id
          );
          if (typeof event.sequence_number === "number") {
            lastEventSequenceRef.current = Math.max(
              lastEventSequenceRef.current ?? 0,
              event.sequence_number
            );
          }
          return;
        }
        if (event.type === "EVENT_REJECTED") {
          if (event.client_event_id) {
            pendingSocketEventsRef.current = pendingSocketEventsRef.current.filter(
              (pending) => pending.client_event_id !== event.client_event_id
            );
          }
          setAiObservation(event.reason ?? "El servidor rechazo un cambio colaborativo.");
          return;
        }
        if (event.type === "PONG") return;
        const sequence = event.sequence_number;
        const previousSequence = lastEventSequenceRef.current;
        const sequenceGap =
          typeof sequence === "number" &&
          previousSequence !== null &&
          sequence > previousSequence + 1;
        if (typeof sequence === "number") {
          lastEventSequenceRef.current = Math.max(previousSequence ?? 0, sequence);
        }
        const affectsCurrentDiagram =
          event.type === "UML_EVENT" &&
          (event.diagram_id === diagramId || event.event_type === "RESTORE_VERSION" || sequenceGap);
        if (!affectsCurrentDiagram) return;
        if (event.event_type === "RESTORE_VERSION") {
          const restoredIds = Array.isArray(event.payload?.restored_diagram_ids)
            ? event.payload.restored_diagram_ids.filter((value): value is string => typeof value === "string")
            : [];
          if (!restoredIds.includes(diagramId)) {
            navigate(
              restoredIds[0]
                ? `/proyectos/${projectId}/uml/${restoredIds[0]}`
                : `/proyectos/${projectId}/colaborativo`,
              { replace: true }
            );
            return;
          }
        }
        if (remoteRefreshTimerRef.current !== null) {
          window.clearTimeout(remoteRefreshTimerRef.current);
        }
        remoteRefreshTimerRef.current = window.setTimeout(() => {
          void refreshDiagramModel().then(() => {
            setSelectedClassId(null);
            setSelectedRelationshipId(null);
            setCanvasRevision((current) => current + 1);
            setAiObservation(`${event.user_name ?? "Otro colaborador"} actualizo el diagrama.`);
          });
        }, 120);
      };
    }

    connect();
    return () => {
      disposed = true;
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer);
      }
      window.clearInterval(heartbeatTimer);
      if (remoteRefreshTimerRef.current !== null) {
        window.clearTimeout(remoteRefreshTimerRef.current);
      }
      socketRef.current?.close();
      socketRef.current = null;
      pendingSocketEventsRef.current = [];
    };
  }, [diagramId, projectId]);

  function publishChange(payload: Record<string, unknown>) {
    const clientEventId = createClientEventId();
    const event = {
      ...payload,
      diagram_id: diagramId,
      client_event_id: clientEventId
    };
    pendingSocketEventsRef.current = [...pendingSocketEventsRef.current, event].slice(-100);
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      sendProjectEvent(socketRef.current, event);
    }
  }

  const selectedClass = classes.find((umlClass) => umlClass.id === selectedClassId) ?? null;
  const selectedRelationship = relationships.find((relationship) => relationship.id === selectedRelationshipId) ?? null;

  useEffect(() => {
    if (selectedRelationship) {
      setRelationshipLabel(selectedRelationship.label ?? "");
      setSourceMultiplicity(selectedRelationship.source_cardinality ?? "");
      setTargetMultiplicity(selectedRelationship.target_cardinality ?? "");
      setRelationshipType(selectedRelationship.relationship_type);
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
      publishChange({ action: "CREATE_CLASS", class_id: created.id });
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
    if (name.trim().length > 0) {
      void umlService.updateClass(classId, { name: name.trim() }).then((updated) => {
        const current = useUmlStore.getState().classes.find((item) => item.id === classId);
        if (current) {
          updateClass({ ...current, ...updated });
        }
        publishChange({ action: "UPDATE_CLASS", class_id: classId });
      });
    }
  }

  async function handleElementTypeChange(nextType: UmlElementType) {
    if (!selectedClass) return;
    try {
      const updated = await umlService.updateClass(
        selectedClass.id,
        { element_type: nextType } as unknown as Parameters<typeof umlService.updateClass>[1]
      );
      updateClass({ ...selectedClass, ...updated, element_type: nextType });
      publishChange({ action: "UPDATE_CLASS", class_id: selectedClass.id });
    } catch {
      setAiObservation("No se pudo actualizar el tipo de elemento.");
    }
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
        source_cardinality: "*",
        target_cardinality: "*",
        metadata_json: { association_class_id: associationClass.id }
      });
      addRelationship(association);
      setSelectedClassId(associationClass.id);
      setSelectedRelationshipId(null);
      setPendingSourceId("");
      setActiveTool("select");
      publishChange({
        action: "CREATE_RELATIONSHIP",
        relationship_id: association.id,
        class_id: associationClass.id
      });
      return;
    }
    const type =
      tool === "inheritance" ||
      tool === "aggregation" ||
      tool === "composition" ||
      tool === "dependency" ||
      tool === "realization"
        ? tool === "realization"
          ? "implementation"
          : tool
        : "association";
    const defaultLabels: Record<string, string> = {
      association: "asocia",
      inheritance: "generaliza",
      aggregation: "agrega",
      composition: "compone",
      dependency: "depende",
      implementation: "realiza"
    };
    const created = await umlService.createRelationship(diagramId, {
      source_class_id: sourceId,
      target_class_id: targetId,
      relationship_type: type,
      label: relationshipLabel.trim() || defaultLabels[type],
      source_cardinality: sourceMultiplicity.trim() || null,
      target_cardinality: targetMultiplicity.trim() || null
    });
    addRelationship(created);
    setSelectedRelationshipId(created.id);
    setSelectedClassId(null);
    setPendingSourceId("");
    setActiveTool("select");
    publishChange({ action: "CREATE_RELATIONSHIP", relationship_id: created.id });
  }

  const handleClassClick = useCallback(
    (classId: string) => {
      if (activeTool !== "select" && activeTool !== "class") {
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
    },
    [activeTool, classes, pendingSourceId, setSelectedClassId]
  );

  const handleRelationshipClick = useCallback((relationshipId: string) => {
    setSelectedRelationshipId(relationshipId);
    setSelectedClassId(null);
    setPendingSourceId("");
    setIsRelationshipModalOpen(true);
  }, [setSelectedClassId]);

  const handleRelationshipDoubleClick = useCallback((relationshipId: string) => {
    setSelectedRelationshipId(relationshipId);
    setSelectedClassId(null);
    setPendingSourceId("");
    setIsRelationshipModalOpen(true);
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
      publishChange({ action: "MOVE_ELEMENT", class_id: classId, position });
    },
    [classes, diagramId, updateClass]
  );

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
    publishChange({ action: "DELETE_CLASS", class_id: selectedClass.id });
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
    publishChange({ action: "UPDATE_RELATIONSHIP", relationship_id: updated.id });
  }

  async function deleteSelectedRelationship() {
    if (!selectedRelationship) {
      return;
    }
    await umlService.deleteRelationship(selectedRelationship.id);
    removeRelationship(selectedRelationship.id);
    setSelectedRelationshipId(null);
    await refreshDiagramModel();
    publishChange({ action: "DELETE_RELATIONSHIP", relationship_id: selectedRelationship.id });
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
    publishChange({ action: "CREATE_ATTRIBUTE", attribute_id: created.id });
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
    publishChange({ action: "UPDATE_ATTRIBUTE", attribute_id: attributeId });
  }

  async function deleteAttribute(attributeId: string) {
    if (!selectedClass) {
      return;
    }
    await umlService.deleteAttribute(attributeId);
    updateClass({ ...selectedClass, attributes: selectedClass.attributes.filter((item) => item.id !== attributeId) });
    publishChange({ action: "DELETE_ATTRIBUTE", attribute_id: attributeId });
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
    publishChange({ action: "CREATE_METHOD", method_id: created.id });
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
    publishChange({ action: "METHOD_SIGNATURE_UPDATED", method_id: methodId });
  }

  async function deleteMethod(methodId: string) {
    if (!selectedClass) {
      return;
    }
    await umlService.deleteMethod(methodId);
    updateClass({ ...selectedClass, methods: selectedClass.methods.filter((item) => item.id !== methodId) });
    publishChange({ action: "DELETE_METHOD", method_id: methodId });
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

  async function applyAiResultToCurrentDiagram(
    aiResult: AiUmlResult,
    sourceType: "text" | "voice" | "image",
    fallbackDescription: string,
    currentModel?: DiagramModel | null
  ) {
    const model = currentModel ?? await refreshDiagramModel();
    const currentClasses = model?.classes ?? useUmlStore.getState().classes;
    const currentRelationships = model?.relationships ?? useUmlStore.getState().relationships;

    await umlService.applyAiModificationToDiagram({
      diagramId,
      classes: currentClasses,
      relationships: currentRelationships,
      result: aiResult
    });
    const updatedModel = await refreshDiagramModel();
    setCanvasRevision((current) => current + 1);
    setSelectedClassId(null);
    setSelectedRelationshipId(null);
    setPendingSourceId("");
    setActiveTool("select");
    publishChange({
      action: "AI_UPDATE_DIAGRAM",
      diagram_id: diagramId,
      source_type: sourceType
    });
    if (sourceType === "image") {
      setAiObservation(
        `${aiResult.engine} incorporo la imagen al diagrama actual. ` +
        `Se conservaron las ${currentClasses.length} clases y ${currentRelationships.length} relaciones previas. ` +
        promptFromAiResult(aiResult, fallbackDescription)
      );
    } else {
      setAiObservation(
        `${aiResult.engine} actualizo este diagrama: ${promptFromAiResult(aiResult, fallbackDescription)}`
      );
    }
    return updatedModel;
  }

  async function generateFromSource(sourceType: "text" | "voice" | "image", file?: File, promptOverride?: string) {
    const basePrompt = promptOverride?.trim() || sourcePrompt.trim() || "Modelo UML generado por IA local";
    if (sourceType === "text" || sourceType === "voice") {
      await modifyCurrentDiagramFromPrompt(basePrompt, sourceType);
      return;
    }
    const aiResult =
      await aiService.imageToUml({
        description: promptOverride?.trim() || undefined,
        image_base64: file ? await fileToBase64(file) : undefined,
        file_name: file?.name
      });
    const unresolvedClasses = aiResult.classes.filter(
      (umlClass) => /^Clase\d+$/i.test(umlClass.name) || !umlClass.name.trim()
    );
    const duplicateClassNames = new Set<string>();
    const seenClassNames = new Set<string>();
    for (const umlClass of aiResult.classes) {
      const normalizedName = umlClass.name.trim().toLocaleLowerCase();
      if (seenClassNames.has(normalizedName)) {
        duplicateClassNames.add(normalizedName);
      }
      seenClassNames.add(normalizedName);
    }
    if (
      aiResult.classes.length === 0 ||
      unresolvedClasses.length > 0 ||
      duplicateClassNames.size > 0 ||
      aiResult.confidence < 0.55
    ) {
      setAiObservation(
        aiResult.observations.join(" ") ||
          "No se pudo leer la imagen con suficiente precision. El diagrama actual no fue modificado."
      );
      return;
    }
    setAiObservation(
      `${aiResult.engine} confianza ${Math.round(aiResult.confidence * 100)}%: ${aiResult.classes
        .map((umlClass) => umlClass.name)
        .join(", ")}`
    );
    await applyAiResultToCurrentDiagram(aiResult, sourceType, "Modelo UML generado desde imagen");
  }

  async function modifyCurrentDiagramFromPrompt(promptOverride?: string, sourceType: "text" | "voice" = "text") {
    const instruction = promptOverride?.trim() || sourcePrompt.trim();
    if (!instruction) {
      setAiObservation("Escriba una instruccion para editar el diagrama actual.");
      return;
    }
    const model = await refreshDiagramModel();
    const currentClasses = model?.classes ?? useUmlStore.getState().classes;
    const currentRelationships = model?.relationships ?? useUmlStore.getState().relationships;
    const selectedClassName =
      currentClasses.find((umlClass) => umlClass.id === selectedClassId)?.name ?? null;
    if (currentClasses.length === 0) {
      const generatedResult =
        sourceType === "voice"
          ? await aiService.voiceToUml({ transcript: instruction })
          : await aiService.textToUml(instruction);
      await applyAiResultToCurrentDiagram(generatedResult, sourceType, instruction, model);
      return;
    }
    const classNameById = new Map(currentClasses.map((umlClass) => [umlClass.id, umlClass.name]));
    const aiResult = await aiService.modifyUml({
      instruction,
      selected_class_name: selectedClassName,
      classes: currentClasses.map((umlClass) => ({
        name: umlClass.name,
        stereotype: umlClass.stereotype,
        attributes: umlClass.attributes.map((attribute) => ({
          name: attribute.name,
          data_type: attribute.data_type,
          visibility: attribute.visibility,
          is_required: attribute.is_required
        })),
        methods: umlClass.methods.map((method) => ({
          name: method.name,
          return_type: method.return_type,
          visibility: method.visibility
        }))
      })),
      relationships: currentRelationships
        .map((relationship) => {
          const source = classNameById.get(relationship.source_class_id);
          const target = classNameById.get(relationship.target_class_id);
          if (!source || !target) {
            return null;
          }
          const associationClassId =
            typeof relationship.metadata_json?.association_class_id === "string"
              ? relationship.metadata_json.association_class_id
              : null;
          const associationClassName = associationClassId ? classNameById.get(associationClassId) : null;
          return {
            source,
            target,
            relationship_type: relationship.relationship_type,
            label: relationship.label,
            source_cardinality: relationship.source_cardinality,
            target_cardinality: relationship.target_cardinality,
            metadata_json: associationClassName
              ? { ...relationship.metadata_json, association_class_name: associationClassName }
              : relationship.metadata_json
          };
        })
        .filter((relationship): relationship is NonNullable<typeof relationship> => relationship !== null)
    });
    await applyAiResultToCurrentDiagram(aiResult, sourceType, instruction, model);
    setAiObservation(
      `${aiResult.engine} edito el diagrama actual: ${
        "changes" in aiResult && aiResult.changes.length > 0
          ? aiResult.changes.join(" ")
          : aiResult.classes.map((umlClass) => umlClass.name).join(", ")
      }`
    );
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
      setAiObservation(`Analizando ${file.name} para incorporarlo al diagrama actual...`);
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
      setSourcePrompt((current) => [current.trim(), transcript.trim()].filter(Boolean).join(" "));
      setAiObservation("Transcripcion lista. Revise el texto y envielo cuando desee editar el diagrama.");
    };
    recognition.onerror = () => {
      setIsListening(false);
      setAiObservation("No se pudo capturar audio desde el navegador.");
    };
    recognition.onend = () => setIsListening(false);
    setIsListening(true);
    recognition.start();
  }

  function activateEditorTool(tool: UmlTool) {
    setPendingSourceId("");
    if (tool === "class") {
      void handleAddClass();
      return;
    }
    setActiveTool(tool);
    if (tool === "select") {
      return;
    }
    const labels: Partial<Record<UmlTool, string>> = {
      association: "asocia",
      inheritance: "generaliza",
      aggregation: "agrega",
      composition: "compone",
      associationClass: "detalle",
      dependency: "depende",
      realization: "realiza"
    };
    setRelationshipLabel(labels[tool] ?? "");
    if (tool === "associationClass") {
      setSourceMultiplicity("*");
      setTargetMultiplicity("*");
    } else if (tool === "inheritance" || tool === "realization") {
      setSourceMultiplicity("1");
      setTargetMultiplicity("1");
    } else if (tool === "aggregation" || tool === "composition") {
      setSourceMultiplicity("0..*");
      setTargetMultiplicity("1");
    } else if (tool === "dependency") {
      setSourceMultiplicity("");
      setTargetMultiplicity("");
    } else {
      setSourceMultiplicity((current) => current || "1");
      setTargetMultiplicity((current) => current || "0..*");
    }
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

  return (
    <section className={cn("uml-editor-scope grid gap-4", isDark ? "uml-editor-dark" : "uml-editor-light")}>
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-teal-100 text-teal-700 dark:bg-teal-500/15 dark:text-teal-300">
            <Network size={23} aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-ink dark:text-white">Editor UML</h1>
            <p className="text-sm text-slate-600 dark:text-slate-300">Canvas colaborativo de diagramas de clases.</p>
          </div>
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
          rightContent={(
            <nav aria-label="Panel lateral del editor" className="grid min-w-[330px] grid-cols-3 gap-1" role="tablist">
              {([
                ["editor", "Editor", PencilRuler],
                ["assistant", "Asistente", Bot],
                ["versions", "Versiones", History],
              ] as const).map(([tab, label, Icon]) => (
                <button
                  aria-selected={rightPanelTab === tab}
                  className={cn(
                    "flex h-9 min-w-0 items-center justify-center gap-1.5 rounded-md px-3 text-xs font-semibold transition",
                    rightPanelTab === tab
                      ? "bg-teal-700 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  )}
                  key={tab}
                  onClick={() => setRightPanelTab(tab)}
                  role="tab"
                  type="button"
                >
                  <Icon className="shrink-0" size={15} aria-hidden="true" />
                  <span className="truncate">{label}</span>
                </button>
              ))}
            </nav>
          )}
        />
        <input ref={imageInputRef} className="hidden" type="file" accept="image/*" onChange={handleImageSelected} />
        <input
          ref={xmiInputRef}
          className="hidden"
          type="file"
          accept=".xml,.xmi,text/xml,application/xml,*/*"
          onChange={handleXmiSelected}
        />
        <div className="grid min-h-[760px] xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="h-[760px] bg-slate-50 dark:bg-slate-900">
            <JointUmlCanvas
              activeTool={activeTool}
              classes={classes}
              isDark={isDark}
              key={`${diagramId}-${canvasRevision}`}
              onClassClick={handleClassClick}
              onClassMove={handleClassMove}
              onClassRename={renameClassInline}
              onRelationshipClick={handleRelationshipClick}
              onRelationshipDoubleClick={handleRelationshipDoubleClick}
              pendingSourceId={pendingSourceId}
              relationships={relationships}
              selectedClassId={selectedClassId}
              selectedRelationshipId={selectedRelationshipId}
            />
          </div>
          <aside className="flex h-[760px] min-h-0 flex-col border-t border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950 xl:border-l xl:border-t-0">
            <div className="min-h-0 flex-1 overflow-hidden p-2">
              <div className={cn("h-full overflow-y-auto", rightPanelTab !== "editor" && "hidden")} role="tabpanel">
                <div className="grid content-start gap-2">
              <section className="overflow-hidden rounded-md border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                <button
                  aria-expanded={elementsExpanded}
                  className="flex h-10 w-full items-center justify-between px-3 text-left text-sm font-bold text-ink hover:bg-slate-50 dark:text-white dark:hover:bg-slate-800"
                  onClick={() => setElementsExpanded((current) => !current)}
                  type="button"
                >
                  Elementos del diagrama
                  <ChevronDown className={cn("transition", !elementsExpanded && "-rotate-90")} size={16} aria-hidden="true" />
                </button>
                {elementsExpanded && (
                  <div className="grid grid-cols-6 gap-2 border-t border-slate-100 p-3 dark:border-slate-700">
                    {([
                      ["select", "Select", MousePointer2],
                      ["class", isCreatingClass ? "Creando" : "Clase", Square],
                      ["association", "Asociacion", ArrowUpRight],
                      ["inheritance", "Generalize", GitBranch],
                      ["associationClass", "Association Class", Table2],
                      ["composition", "Compose", Diamond],
                      ["aggregation", "Aggregate", Diamond],
                      ["dependency", "Dependencia", ArrowUpRight],
                      ["realization", "Realizacion", GitBranch]
                    ] as const).map(([tool, label, Icon]) => {
                      const active = activeTool === tool;
                      return (
                        <button
                          aria-label={label}
                          className={cn(
                            "flex min-h-[72px] min-w-0 flex-col items-center justify-center gap-2 rounded-md border px-1 py-2 text-center text-[11px] font-semibold leading-3 transition",
                            ["select", "class", "composition", "aggregation", "dependency", "realization"].includes(tool)
                              ? "col-span-3"
                              : "col-span-2",
                            active
                              ? "border-teal-500 bg-teal-50 text-teal-800 shadow-sm dark:border-teal-400 dark:bg-teal-500/15 dark:text-teal-200"
                              : "border-slate-200 bg-white text-slate-700 hover:border-teal-300 hover:bg-teal-50/60 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200 dark:hover:border-teal-700 dark:hover:bg-teal-950/30"
                          )}
                          disabled={tool === "class" && isCreatingClass}
                          key={tool}
                          onClick={() => activateEditorTool(tool)}
                          title={label}
                          type="button"
                        >
                          <Icon
                            className={cn("shrink-0", tool === "composition" && "fill-current")}
                            size={21}
                            aria-hidden="true"
                          />
                          <span className="max-w-full">{label}</span>
                        </button>
                      );
                    })}
                    <p className="col-span-6 mt-1 border-t border-slate-100 pt-2 text-xs leading-4 text-slate-500 dark:border-slate-700 dark:text-slate-400">
                      {pendingSourceId
                        ? "Origen seleccionado. Elija la clase destino."
                        : activeTool === "select"
                          ? "Arrastre clases o seleccione una relacion."
                          : "Seleccione la clase origen y luego la clase destino."}
                    </p>
                  </div>
                )}
              </section>

              <section className="overflow-hidden rounded-md border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                <button
                  aria-expanded={editingToolsExpanded}
                  className="flex h-10 w-full items-center justify-between px-3 text-left text-sm font-bold text-ink hover:bg-slate-50 dark:text-white dark:hover:bg-slate-800"
                  onClick={() => setEditingToolsExpanded((current) => !current)}
                  type="button"
                >
                  Herramientas de edicion
                  <ChevronDown className={cn("transition", !editingToolsExpanded && "-rotate-90")} size={16} aria-hidden="true" />
                </button>
                {editingToolsExpanded && <div className="grid gap-3 border-t border-slate-100 p-3 dark:border-slate-700">
                <textarea
                  aria-label="Instruccion para editar el diagrama"
                  className="min-h-24 resize-none rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                  placeholder="Escriba o dicte una instruccion..."
                  value={sourcePrompt}
                  onChange={(event) => setSourcePrompt(event.target.value)}
                />
                <div className="grid grid-cols-3 gap-2">
                  <Button
                    aria-label={isListening ? "Escuchando dictado" : "Iniciar dictado por voz"}
                    className="w-full px-0"
                    disabled={isListening}
                    icon={<Mic className={isListening ? "animate-pulse" : ""} size={18} aria-hidden="true" />}
                    onClick={generateFromVoiceCapture}
                    title={isListening ? "Escuchando" : "Transcribir por voz"}
                    variant="secondary"
                  >
                    <span className="sr-only">{isListening ? "Escuchando" : "Voz"}</span>
                  </Button>
                  <Button
                    aria-label="Enviar instruccion de edicion"
                    className="w-full px-0"
                    disabled={!sourcePrompt.trim()}
                    icon={<Send size={18} aria-hidden="true" />}
                    onClick={() => modifyCurrentDiagramFromPrompt()}
                    title="Editar diagrama"
                    variant="secondary"
                  >
                    <span className="sr-only">Editar</span>
                  </Button>
                  <Button
                    aria-label="Incorporar diagrama desde imagen"
                    className="w-full px-0"
                    icon={<Image size={18} aria-hidden="true" />}
                    onClick={() => imageInputRef.current?.click()}
                    title="Incorporar imagen al diagrama actual"
                    variant="secondary"
                  >
                    <span className="sr-only">Imagen</span>
                  </Button>
                </div>
                {aiObservation ? <p className="text-xs leading-5 text-slate-600 dark:text-slate-300" role="status">{aiObservation}</p> : null}
                </div>}
              </section>
                </div>
              </div>
              <div className={cn("h-full min-h-0", rightPanelTab !== "assistant" && "hidden")} role="tabpanel">
                <ProjectAiAssistant
                  diagramId={diagramId}
                  initialConversationId={requestedChatId}
                  mode="embedded"
                  projectId={projectId}
                />
              </div>
              <div className={cn("h-full min-h-0", rightPanelTab !== "versions" && "hidden")} role="tabpanel">
                <ProjectHistoryPanel
                  mode="embedded"
                  projectId={projectId}
                  onVersionRestored={async (result) => {
                    if (!result.restored_diagram_ids.includes(diagramId)) {
                      const destination = result.restored_diagram_ids[0];
                      navigate(
                        destination
                          ? `/proyectos/${projectId}/uml/${destination}`
                          : `/proyectos/${projectId}/colaborativo`,
                        { replace: true }
                      );
                      return;
                    }
                    await refreshDiagramModel();
                    setCanvasRevision((current) => current + 1);
                  }}
                />
              </div>
            </div>
          </aside>
        </div>

        <div className="border-t border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900">
          <Panel className="overflow-hidden p-0 dark:border-slate-700 dark:bg-slate-950">
            <div className="p-4 pb-0">
            <div className="flex flex-col justify-between gap-2 md:flex-row md:items-center">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-teal-50 text-teal-700 dark:bg-teal-500/15 dark:text-teal-300">
                  <SlidersHorizontal size={20} aria-hidden="true" />
                </span>
                <div>
                  <h2 className="text-lg font-bold text-ink dark:text-white">Propiedades del elemento</h2>
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    {selectedClass ? `${selectedClass.name}: atributos y metodos editables` : "Seleccione una clase para editar atributos y metodos."}
                  </p>
                </div>
              </div>
              <div className="rounded-md border border-slate-200 px-3 py-2 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300">
                {relationships.length} relaciones en el diagrama
              </div>
            </div>

            <nav aria-label="Detalles del elemento" className="mt-3 flex border-b border-slate-200 dark:border-slate-700" role="tablist">
              {([
                ["properties", "Propiedades del elemento", Settings2],
                ["relationships", "Relaciones", Link2]
              ] as const).map(([tab, label, Icon]) => (
                <button
                  aria-selected={elementDetailsTab === tab}
                  className={cn(
                    "flex h-10 items-center gap-2 border-b-2 px-4 text-xs font-semibold transition",
                    elementDetailsTab === tab
                      ? "border-teal-600 text-teal-700 dark:border-teal-400 dark:text-teal-300"
                      : "border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
                  )}
                  key={tab}
                  onClick={() => setElementDetailsTab(tab)}
                  role="tab"
                  type="button"
                >
                  <Icon size={15} aria-hidden="true" />
                  {label}
                </button>
              ))}
            </nav>
            </div>

            {elementDetailsTab === "properties" ? (
            <div className="grid gap-3 p-4 pt-3" role="tabpanel">
              {selectedClass && (
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
                  <ElementTypeSelect
                    value={selectedClass.element_type}
                    onChange={handleElementTypeChange}
                  />
                  {selectedClass.element_type === "enum" && (
                    <span className="text-xs text-amber-700 dark:text-amber-300">
                      En los enumerados, los atributos se definen como literales y los metodos se omiten.
                    </span>
                  )}
                </div>
              )}
              <div className="grid gap-3 xl:grid-cols-2">
              <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-700">
                <div className="flex min-h-11 items-center justify-between gap-3 border-b border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                  <div className="flex items-center gap-2 font-semibold text-ink dark:text-white">
                    <List className="text-indigo-600 dark:text-indigo-300" size={18} aria-hidden="true" />
                    {selectedClass?.element_type === "enum" ? "Literales" : "Atributos"}
                  </div>
                  <Button
                    className="h-8 px-3 text-xs"
                    disabled={!selectedClass}
                    icon={<Plus size={14} aria-hidden="true" />}
                    onClick={() => attributeNameInputRef.current?.focus()}
                    variant="secondary"
                  >
                    {selectedClass?.element_type === "enum" ? "Agregar literal" : "Agregar atributo"}
                  </Button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[500px] text-left text-sm">
                    <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                      <tr>
                        <th className="w-24 px-3 py-2">Vis.</th>
                        <th className="px-3 py-2">Nombre</th>
                        <th className="px-3 py-2">Tipo</th>
                        <th className="w-24 px-3 py-2">Acciones</th>
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
                            <div className="grid w-full grid-cols-2 gap-2">
                              <Button
                                aria-label="Guardar atributo"
                                className="h-9 w-full min-w-9 !p-0"
                                icon={<Save className="h-4 w-4 shrink-0" aria-hidden="true" />}
                                onClick={() => saveAttribute(attribute.id)}
                                title="Guardar atributo"
                                variant="secondary"
                              />
                              <Button
                                aria-label="Eliminar atributo"
                                className="h-9 w-full min-w-9 !p-0"
                                icon={<Trash2 className="h-4 w-4 shrink-0" aria-hidden="true" />}
                                onClick={() => deleteAttribute(attribute.id)}
                                title="Eliminar atributo"
                                variant="danger"
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td className="px-3 py-2 text-slate-500 dark:text-slate-400">{visibilitySymbol("private")} Privado</td>
                        <td className="px-3 py-2">
                          <input
                            ref={attributeNameInputRef}
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
                <div className="flex min-h-11 items-center justify-between gap-3 border-b border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                  <div className="flex items-center gap-2 font-semibold text-ink dark:text-white">
                    <Settings2 className="text-indigo-600 dark:text-indigo-300" size={18} aria-hidden="true" />
                    Metodos
                  </div>
                  {selectedClass?.element_type !== "enum" && (
                    <Button
                      className="h-8 px-3 text-xs"
                      disabled={!selectedClass}
                      icon={<Plus size={14} aria-hidden="true" />}
                      onClick={() => methodNameInputRef.current?.focus()}
                      variant="secondary"
                    >
                      Agregar metodo
                    </Button>
                  )}
                </div>
                {selectedClass?.element_type === "enum" ? (
                  <div className="flex h-36 items-center justify-center p-4 text-xs italic text-slate-500 dark:text-slate-400">
                    Los enumerados en UML no contienen metodos.
                  </div>
                ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[500px] text-left text-sm">
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
                            <div className="grid w-full grid-cols-3 gap-2">
                              <Button
                                aria-label="Guardar metodo"
                                className="h-9 w-full min-w-9 !p-0"
                                icon={<Save className="h-4 w-4 shrink-0" aria-hidden="true" />}
                                onClick={() => saveMethod(method.id)}
                                title="Guardar metodo"
                                variant="secondary"
                              />
                              <Button
                                aria-label="Especificar metodo"
                                className="h-9 w-full min-w-9 !p-0"
                                icon={<Eye className="h-[18px] w-[18px] shrink-0" aria-hidden="true" />}
                                onClick={() => setSpecificationMethodId(method.id)}
                                title="Especificar metodo"
                                variant="secondary"
                              />
                              <Button
                                aria-label="Eliminar metodo"
                                className="h-9 w-full min-w-9 !p-0"
                                icon={<Trash2 className="h-4 w-4 shrink-0" aria-hidden="true" />}
                                onClick={() => deleteMethod(method.id)}
                                title="Eliminar metodo"
                                variant="danger"
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td className="px-3 py-2 text-slate-500 dark:text-slate-400">{visibilitySymbol("public")} Publico</td>
                        <td className="px-3 py-2">
                          <input
                            ref={methodNameInputRef}
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
                )}
              </div>
            </div>
          </div>
            ) : (
              <div className="p-4 pt-3" role="tabpanel">
                {relationships.length === 0 ? (
                  <div className="flex min-h-32 flex-col items-center justify-center gap-2 rounded-md border border-dashed border-slate-300 px-4 text-center dark:border-slate-700">
                    <Link2 className="text-slate-400" size={24} aria-hidden="true" />
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">El diagrama no tiene relaciones</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">Cree una relacion desde las herramientas del editor.</p>
                  </div>
                ) : (
                  <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-700">
                    <div className="flex min-h-11 items-center gap-2 border-b border-slate-200 bg-white px-3 py-2 font-semibold text-ink dark:border-slate-700 dark:bg-slate-900 dark:text-white">
                      <Link2 className="text-indigo-600 dark:text-indigo-300" size={18} aria-hidden="true" />
                      Relaciones del diagrama
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full min-w-[720px] text-left text-sm">
                        <thead className="bg-slate-100 text-xs uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                          <tr>
                            <th className="px-3 py-2">Origen</th>
                            <th className="px-3 py-2">Tipo</th>
                            <th className="px-3 py-2">Destino</th>
                            <th className="px-3 py-2">Multiplicidad</th>
                            <th className="w-24 px-3 py-2 text-center">Acciones</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-950">
                          {relationships.map((relationship) => (
                            <tr key={relationship.id}>
                              <td className="px-3 py-2 font-medium text-slate-800 dark:text-slate-100">
                                {classes.find((item) => item.id === relationship.source_class_id)?.name ?? "Clase no disponible"}
                              </td>
                              <td className="px-3 py-2 capitalize text-slate-600 dark:text-slate-300">
                                {relationship.relationship_type}
                              </td>
                              <td className="px-3 py-2 font-medium text-slate-800 dark:text-slate-100">
                                {classes.find((item) => item.id === relationship.target_class_id)?.name ?? "Clase no disponible"}
                              </td>
                              <td className="px-3 py-2 text-slate-600 dark:text-slate-300">
                                {relationship.source_cardinality || "-"} / {relationship.target_cardinality || "-"}
                              </td>
                              <td className="px-3 py-2">
                                <Button
                                  aria-label="Editar relacion"
                                  className="mx-auto h-8 min-w-9 !p-0"
                                  icon={<Eye size={16} aria-hidden="true" />}
                                  onClick={() => {
                                    setSelectedRelationshipId(relationship.id);
                                    setSelectedClassId(null);
                                    setIsRelationshipModalOpen(true);
                                  }}
                                  title="Editar relacion"
                                  variant="secondary"
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Panel>
        </div>
      </Panel>

      {isRelationshipModalOpen && selectedRelationship && (
        <div
          className={cn(
            "fixed inset-0 z-50 flex items-center justify-center px-4",
            isDark ? "bg-slate-950/65" : "bg-slate-900/25"
          )}
        >
          <div
            className={cn(
              "w-full max-w-md rounded-lg border shadow-2xl",
              isDark ? "border-slate-700 bg-slate-950 text-slate-100" : "border-slate-200 bg-white text-slate-950"
            )}
          >
            <div className={cn("flex items-center justify-between border-b px-5 py-4", isDark ? "border-slate-700" : "border-slate-200")}>
              <div>
                <h2 className={cn("text-lg font-semibold", isDark ? "text-white" : "text-slate-950")}>Propiedades de relacion</h2>
                <p className={cn("text-sm", isDark ? "text-slate-400" : "text-slate-500")}>
                  El extremo destino recibe la flecha, triangulo o diamante. Puede definir multiplicidad en ambos extremos.
                </p>
              </div>
              <button
                className={cn(
                  "rounded-md p-2 transition",
                  isDark ? "text-slate-300 hover:bg-slate-800" : "text-slate-500 hover:bg-slate-100"
                )}
                onClick={() => setIsRelationshipModalOpen(false)}
                type="button"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="grid gap-4 px-5 py-4">
              <label className={cn("grid gap-1.5 text-sm font-medium", isDark ? "text-slate-200" : "text-slate-700")}>
                Tipo de relacion
                <select
                  className={cn(
                    "h-10 rounded-md border px-3 text-sm outline-none transition focus:border-accent focus:ring-2",
                    isDark
                      ? "border-slate-700 bg-slate-900 text-slate-100 focus:ring-teal-900/50"
                      : "border-slate-300 bg-white text-slate-950 focus:ring-teal-100"
                  )}
                  value={relationshipType}
                  onChange={(event) => setRelationshipType(event.target.value)}
                >
                  {relationshipTypeOptions.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label className={cn("grid gap-1.5 text-sm font-medium", isDark ? "text-slate-200" : "text-slate-700")}>
                Etiqueta
                <input
                  className={cn(
                    "h-10 rounded-md border px-3 text-sm outline-none transition focus:border-accent focus:ring-2",
                    isDark
                      ? "border-slate-700 bg-slate-900 text-slate-100 placeholder:text-slate-500 focus:ring-teal-900/50"
                      : "border-slate-300 bg-white text-slate-950 placeholder:text-slate-400 focus:ring-teal-100"
                  )}
                  value={relationshipLabel}
                  onChange={(event) => setRelationshipLabel(event.target.value)}
                />
              </label>
              <div className="grid grid-cols-2 gap-3">
                  <label className={cn("grid gap-1 text-xs font-semibold", isDark ? "text-slate-300" : "text-slate-600")}>
                    Origen
                    <select
                      className={cn(
                        "h-10 rounded-md border px-3 text-sm outline-none",
                        isDark ? "border-slate-700 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-950"
                      )}
                      value={sourceMultiplicity}
                      onChange={(event) => setSourceMultiplicity(event.target.value)}
                    >
                      {multiplicityOptions.map((option) => (
                        <option key={`modal-source-${option || "none"}`} value={option}>
                          {option || "Sin definir"}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className={cn("grid gap-1 text-xs font-semibold", isDark ? "text-slate-300" : "text-slate-600")}>
                    Destino
                    <select
                      className={cn(
                        "h-10 rounded-md border px-3 text-sm outline-none",
                        isDark ? "border-slate-700 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-950"
                      )}
                      value={targetMultiplicity}
                      onChange={(event) => setTargetMultiplicity(event.target.value)}
                    >
                      {multiplicityOptions.map((option) => (
                        <option key={`modal-target-${option || "none"}`} value={option}>
                          {option || "Sin definir"}
                        </option>
                      ))}
                    </select>
                  </label>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  className={cn(
                    "inline-flex h-10 items-center justify-center gap-2 rounded-md border px-4 text-sm font-medium transition",
                    isDark
                      ? "border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
                      : "border-slate-300 bg-white text-slate-900 hover:bg-slate-50"
                  )}
                  onClick={async () => {
                    await saveSelectedRelationship();
                    setIsRelationshipModalOpen(false);
                  }}
                  type="button"
                >
                  <Save size={16} aria-hidden="true" />
                  Guardar
                </button>
                <button
                  className={cn(
                    "inline-flex h-10 items-center justify-center rounded-md border px-4 text-sm font-medium transition",
                    isDark
                      ? "border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
                      : "border-slate-300 bg-white text-slate-900 hover:bg-slate-50"
                  )}
                  onClick={() => setIsRelationshipModalOpen(false)}
                  type="button"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {specificationMethodId && selectedClass && (() => {
        const method = selectedClass.methods.find((item) => item.id === specificationMethodId);
        return method ? (
          <MethodSpecificationEditor
            projectId={projectId}
            diagramId={diagramId}
            umlClass={selectedClass}
            classes={classes}
            method={method}
            dark={isDark}
            onClose={() => setSpecificationMethodId(null)}
            onMethodChange={(updated) => updateClass({
              ...selectedClass,
              methods: selectedClass.methods.map((item) => item.id === updated.id ? updated : item)
            })}
          />
        ) : null;
      })()}

      {showValidationModal && validation && (
        <div
          className={cn(
            "fixed inset-0 z-50 flex items-center justify-center px-4",
            isDark ? "bg-slate-950/65" : "bg-slate-900/25"
          )}
        >
          <div
            className={cn(
              "w-full max-w-lg rounded-lg border shadow-2xl",
              isDark ? "border-slate-700 bg-slate-950 text-slate-100" : "border-slate-200 bg-white text-slate-950"
            )}
          >
            <div className={cn("flex items-center justify-between border-b px-5 py-4", isDark ? "border-slate-700" : "border-slate-200")}>
              <div>
                <h2 className={cn("text-lg font-semibold", isDark ? "text-white" : "text-slate-950")}>Validacion UML</h2>
                <p className={cn("text-sm", isDark ? "text-slate-400" : "text-slate-500")}>Resultado del analisis del diagrama.</p>
              </div>
              <button
                className={cn(
                  "rounded-md p-2 transition",
                  isDark ? "text-slate-300 hover:bg-slate-800" : "text-slate-500 hover:bg-slate-100"
                )}
                onClick={() => setShowValidationModal(false)}
                type="button"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
            <div className="grid gap-4 px-5 py-4 text-sm">
              <div className="grid grid-cols-3 gap-2">
                <div className={cn("rounded-md border p-3", isDark ? "border-slate-700 bg-slate-900" : "border-slate-200 bg-white")}>
                  <p className={cn("text-xs", isDark ? "text-slate-400" : "text-slate-500")}>Errores</p>
                  <p className="text-xl font-semibold text-rose-600">{validation.errors.length}</p>
                </div>
                <div className={cn("rounded-md border p-3", isDark ? "border-slate-700 bg-slate-900" : "border-slate-200 bg-white")}>
                  <p className={cn("text-xs", isDark ? "text-slate-400" : "text-slate-500")}>Advertencias</p>
                  <p className="text-xl font-semibold text-amber-600">{validation.warnings.length}</p>
                </div>
                <div className={cn("rounded-md border p-3", isDark ? "border-slate-700 bg-slate-900" : "border-slate-200 bg-white")}>
                  <p className={cn("text-xs", isDark ? "text-slate-400" : "text-slate-500")}>Recomendaciones</p>
                  <p className="text-xl font-semibold text-accent">{validation.recommendations.length}</p>
                </div>
              </div>
              {[...validation.errors, ...validation.warnings, ...validation.recommendations].length > 0 ? (
                <ul className={cn("max-h-56 list-disc overflow-auto pl-5", isDark ? "text-slate-200" : "text-slate-700")}>
                  {validation.errors.map((item) => <li key={`error-${item}`}>{item}</li>)}
                  {validation.warnings.map((item) => <li key={`warning-${item}`}>{item}</li>)}
                  {validation.recommendations.map((item) => <li key={`recommendation-${item}`}>{item}</li>)}
                </ul>
              ) : (
                <p className={cn("rounded-md px-3 py-2", isDark ? "bg-teal-500/10 text-slate-200" : "bg-teal-50 text-slate-700")}>
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
