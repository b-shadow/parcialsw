import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  type Edge,
  type Node,
  type NodeDragHandler,
  type NodeMouseHandler
} from "reactflow";
import "reactflow/dist/style.css";
import { useParams } from "react-router-dom";
import { Link2, Save, Trash2, Wifi } from "lucide-react";

import { createProjectSocket, sendProjectEvent } from "../../../core/websocket/projectSocket";
import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { UmlClassNode } from "../components/UmlClassNode";
import { UmlToolbar } from "../components/UmlToolbar";
import { aiService } from "../services/aiService";
import { umlService } from "../services/umlService";
import { useUmlStore } from "../store/umlStore";

const nodeTypes = { umlClass: UmlClassNode };

export function UmlEditorPage() {
  const { projectId = "", diagramId = "" } = useParams();
  const socketRef = useRef<WebSocket | null>(null);
  const classes = useUmlStore((state) => state.classes);
  const relationships = useUmlStore((state) => state.relationships);
  const validation = useUmlStore((state) => state.validation);
  const selectedClassId = useUmlStore((state) => state.selectedClassId);
  const setClasses = useUmlStore((state) => state.setClasses);
  const addClass = useUmlStore((state) => state.addClass);
  const updateClass = useUmlStore((state) => state.updateClass);
  const removeClass = useUmlStore((state) => state.removeClass);
  const addRelationship = useUmlStore((state) => state.addRelationship);
  const setRelationships = useUmlStore((state) => state.setRelationships);
  const setValidation = useUmlStore((state) => state.setValidation);
  const setSelectedClassId = useUmlStore((state) => state.setSelectedClassId);
  const [className, setClassName] = useState("Cliente");
  const [sourcePrompt, setSourcePrompt] = useState("Crear sistema de biblioteca con libros, usuarios y prestamos");
  const [aiObservation, setAiObservation] = useState("Motor IA local listo.");
  const [xmiContent, setXmiContent] = useState("");
  const [connectionStatus, setConnectionStatus] = useState("desconectado");

  useEffect(() => {
    umlService
      .getDiagramModel(diagramId)
      .then((model) => {
        setClasses(model.classes);
        setRelationships(model.relationships);
      })
      .catch(() => {
        setClasses([]);
        setRelationships([]);
      });
  }, [diagramId, setClasses, setRelationships]);

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

  const nodes: Node[] = useMemo(
    () =>
      classes.map((umlClass, index) => ({
        id: umlClass.id,
        type: "umlClass",
        position: {
          x: umlClass.visual?.position_x ?? 80 + index * 260,
          y: umlClass.visual?.position_y ?? 80 + (index % 3) * 170
        },
        data: {
          name: umlClass.name,
          stereotype: umlClass.stereotype,
          attributes: umlClass.attributes.map(
            (attribute) => `${attribute.visibility === "private" ? "-" : "+"} ${attribute.name}: ${attribute.data_type}`
          ),
          methods: umlClass.methods.map(
            (method) => `${method.visibility === "private" ? "-" : "+"} ${method.name}(): ${method.return_type ?? "void"}`
          )
        }
      })),
    [classes]
  );

  const edges: Edge[] = useMemo(
    () =>
      relationships.map((relationship) => ({
        id: relationship.id,
        source: relationship.source_class_id,
        target: relationship.target_class_id,
        label: relationship.label ?? relationship.relationship_type,
        animated: relationship.relationship_type === "dependency"
      })),
    [relationships]
  );

  const selectedClass = classes.find((umlClass) => umlClass.id === selectedClassId) ?? null;

  async function handleAddClass() {
    const created = await umlService.createClass(diagramId, {
      name: className.trim() || `Clase${classes.length + 1}`,
      position_x: 80 + classes.length * 260,
      position_y: 100 + (classes.length % 3) * 170
    });
    addClass({ ...created, attributes: [], methods: [], visual: null });
    sendProjectEvent(socketRef.current, { action: "CREATE_CLASS", class_id: created.id });
  }

  async function handleValidate() {
    setValidation(await umlService.validate(diagramId));
  }

  async function handleCreateRelationship() {
    if (classes.length < 2) {
      return;
    }
    const created = await umlService.createRelationship(diagramId, {
      source_class_id: classes[0].id,
      target_class_id: classes[1].id,
      relationship_type: "association",
      label: "usa"
    });
    addRelationship(created);
    sendProjectEvent(socketRef.current, { action: "CREATE_RELATIONSHIP", relationship_id: created.id });
  }

  const handleNodeClick: NodeMouseHandler = useCallback(
    (_, node) => {
      setSelectedClassId(node.id);
    },
    [setSelectedClassId]
  );

  const handleNodeDragStop: NodeDragHandler = useCallback(
    (_, node) => {
      void umlService.moveElement(diagramId, {
        element_type: "class",
        element_id: node.id,
        position_x: node.position.x,
        position_y: node.position.y
      });
      sendProjectEvent(socketRef.current, { action: "MOVE_ELEMENT", class_id: node.id, position: node.position });
    },
    [diagramId]
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
    await umlService.deleteClass(selectedClass.id);
    removeClass(selectedClass.id);
    setSelectedClassId(null);
    sendProjectEvent(socketRef.current, { action: "DELETE_CLASS", class_id: selectedClass.id });
  }

  async function generateFromSource(sourceType: "text" | "voice" | "image") {
    const aiResult =
      sourceType === "text"
        ? await aiService.textToUml(sourcePrompt)
        : sourceType === "voice"
          ? await aiService.voiceToUml(sourcePrompt)
          : await aiService.imageToUml(sourcePrompt);
    setAiObservation(
      `${aiResult.engine} confianza ${Math.round(aiResult.confidence * 100)}%: ${aiResult.classes
        .map((umlClass) => umlClass.name)
        .join(", ")}`
    );
    const generated = await umlService.generate({
      project_id: projectId,
      name: `UML generado ${sourceType}`,
      prompt: sourcePrompt,
      source_type: sourceType
    });
    window.location.href = `/proyectos/${projectId}/uml/${generated.id}`;
  }

  async function importXmi() {
    const imported = await umlService.importXmi({
      project_id: projectId,
      name: "Modelo importado XMI",
      file_name: "modelo-importado.xmi",
      content: xmiContent
    });
    window.location.href = `/proyectos/${projectId}/uml/${imported.id}`;
  }

  function exportXmi() {
    void umlService.exportXmi(diagramId).then((xmi) => {
      const blob = new Blob([xmi.content], { type: "application/xml" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = xmi.file_name;
      anchor.click();
      URL.revokeObjectURL(url);
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
    <section className="grid gap-4">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-semibold">Editor UML</h1>
          <p className="mt-1 text-sm text-slate-600">Canvas colaborativo de diagrama de clases.</p>
        </div>
        <StatusBadge tone={connectionStatus === "conectado" ? "success" : "warning"}>
          {connectionStatus}
        </StatusBadge>
      </div>

      <Panel className="overflow-hidden">
        <UmlToolbar onAddClass={handleAddClass} onValidate={handleValidate} onExport={exportXmi} />
        <div className="grid min-h-[680px] lg:grid-cols-[1fr_320px]">
          <div className="h-[680px] bg-slate-50">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodeClick={handleNodeClick}
              onNodeDragStop={handleNodeDragStop}
              fitView
            >
              <Background />
              <Controls />
              <MiniMap />
            </ReactFlow>
          </div>
          <aside className="border-t border-slate-200 bg-white p-4 lg:border-l lg:border-t-0">
            <div className="grid gap-4">
              <Input label="Nombre de clase" value={className} onChange={(event) => setClassName(event.target.value)} />
              <div className="grid grid-cols-2 gap-2">
                <Button icon={<Save size={18} aria-hidden="true" />} onClick={saveSelectedClass} variant="secondary">
                  Guardar
                </Button>
                <Button icon={<Trash2 size={18} aria-hidden="true" />} onClick={deleteSelectedClass} variant="danger">
                  Eliminar
                </Button>
              </div>
              <Button icon={<Link2 size={18} aria-hidden="true" />} onClick={handleCreateRelationship} variant="secondary">
                Relacion
              </Button>
              <Panel className="p-4">
                <h2 className="text-sm font-semibold">Propiedades</h2>
                <p className="mt-2 text-sm text-slate-600">{selectedClass?.name ?? "Seleccione una clase"}</p>
              </Panel>
              <Panel className="p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Wifi className="text-accent" size={18} aria-hidden="true" />
                  <h2 className="text-sm font-semibold">Validacion</h2>
                </div>
                <p className="text-sm text-slate-600">Errores: {validation?.errors.length ?? 0}</p>
                <p className="text-sm text-slate-600">Advertencias: {validation?.warnings.length ?? 0}</p>
                <p className="text-sm text-slate-600">Recomendaciones: {validation?.recommendations.length ?? 0}</p>
              </Panel>
              <Panel className="grid gap-3 p-4">
                <h2 className="text-sm font-semibold">IA local preparada</h2>
                <textarea
                  className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm"
                  value={sourcePrompt}
                  onChange={(event) => setSourcePrompt(event.target.value)}
                />
                <div className="grid grid-cols-3 gap-2">
                  <Button onClick={() => generateFromSource("text")} variant="secondary">Texto</Button>
                  <Button onClick={() => generateFromSource("voice")} variant="secondary">Voz</Button>
                  <Button onClick={() => generateFromSource("image")} variant="secondary">Imagen</Button>
                </div>
                <p className="text-xs leading-5 text-slate-600">{aiObservation}</p>
              </Panel>
              <Panel className="grid gap-3 p-4">
                <h2 className="text-sm font-semibold">XMI</h2>
                <textarea
                  className="min-h-24 rounded-md border border-slate-300 px-3 py-2 text-sm"
                  placeholder="<xmi:XMI>...</xmi:XMI>"
                  value={xmiContent}
                  onChange={(event) => setXmiContent(event.target.value)}
                />
                <div className="grid grid-cols-2 gap-2">
                  <Button onClick={importXmi} variant="secondary">Importar</Button>
                  <Button onClick={exportJsonSnapshot} variant="ghost">JSON</Button>
                </div>
              </Panel>
            </div>
          </aside>
        </div>
      </Panel>
    </section>
  );
}
