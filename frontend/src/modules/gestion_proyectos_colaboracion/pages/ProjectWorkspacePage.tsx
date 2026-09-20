import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  CalendarDays,
  ChevronDown,
  ChevronRight,
  FileText,
  FileUp,
  FolderTree,
  Image,
  Layers3,
  Mic,
  Pencil,
  PlusCircle,
  Save,
  Search,
  Settings,
  Sparkles,
  Trash2,
  Upload,
  Users,
} from "lucide-react";

import { cn } from "../../../shared/utils/cn";
import { aiService } from "../../modelado_uml_inteligente/services/aiService";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import type { UmlDiagram } from "../../modelado_uml_inteligente/types/uml";
import { projectService } from "../services/projectService";
import { useProjectStore } from "../store/projectStore";
import type { ProjectMember } from "../types/project";

type AiUmlResult = Awaited<ReturnType<typeof aiService.textToUml>>;

const inputClass = "collab-field h-11 w-full rounded-md border px-3 text-sm outline-none transition focus:ring-2";
const textareaClass = "collab-field min-h-24 w-full rounded-md border px-3 py-2 text-sm outline-none transition focus:ring-2";
const buttonBase =
  "inline-flex h-11 items-center justify-center gap-2 rounded-md px-4 text-sm font-black transition disabled:cursor-not-allowed disabled:opacity-60";

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
  return [fallback, classNames.length > 0 ? `Clases: ${classNames.join(", ")}` : "", relations ? `Relaciones: ${relations}` : ""]
    .filter(Boolean)
    .join(". ");
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

function diagramTypeLabel(type: string) {
  return type === "class" ? "Diagrama de clases" : type;
}

function statusLabel(status: string) {
  return status === "active" ? "Actualizado" : status === "review" ? "En revision" : status;
}

function memberInitial(value: string) {
  return value.slice(0, 2).toUpperCase();
}

function statusClassName(status: string) {
  if (status === "active") {
    return "collab-status collab-status-success";
  }
  return "collab-status collab-status-warning";
}

export function ProjectWorkspacePage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const activeProject = useProjectStore((state) => state.activeProject);
  const setActiveProject = useProjectStore((state) => state.setActiveProject);
  const [diagrams, setDiagrams] = useState<UmlDiagram[]>([]);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [diagramName, setDiagramName] = useState("");
  const [sourcePrompt, setSourcePrompt] = useState("");
  const [xmiContent, setXmiContent] = useState("");
  const [operationMessage, setOperationMessage] = useState("Motor IA local listo.");
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const imageInputRef = useRef<HTMLInputElement | null>(null);
  const xmiInputRef = useRef<HTMLInputElement | null>(null);
  const projectReady = useMemo(() => Boolean(projectId), [projectId]);

  useEffect(() => {
    if (!projectReady) {
      return;
    }
    projectService.get(projectId).then(setActiveProject).catch(() => undefined);
    projectService.members(projectId).then(setMembers).catch(() => undefined);
    umlService.listDiagrams(projectId).then(setDiagrams).catch(() => undefined);
  }, [projectId, projectReady, setActiveProject]);

  const diagramTypes = useMemo(() => Array.from(new Set(diagrams.map((diagram) => diagram.diagram_type))).filter(Boolean), [diagrams]);
  const filteredDiagrams = useMemo(
    () =>
      diagrams.filter((diagram) => {
        const matchesSearch =
          diagram.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (diagram.description ?? "").toLowerCase().includes(searchTerm.toLowerCase());
        const matchesType = typeFilter === "all" || diagram.diagram_type === typeFilter;
        return matchesSearch && matchesType;
      }),
    [diagrams, searchTerm, typeFilter]
  );

  async function createDiagram(event: FormEvent) {
    event.preventDefault();
    if (diagramName.trim().length < 2 || isProcessing) {
      return;
    }
    setIsProcessing(true);
    try {
      const diagram = await umlService.createDiagram({
        project_id: projectId,
        name: diagramName,
        description: activeProject?.description ?? undefined,
      });
      setDiagrams((current) => [diagram, ...current]);
      setDiagramName("");
      setOperationMessage(`Diagrama creado: ${diagram.name}`);
    } finally {
      setIsProcessing(false);
    }
  }

  async function deleteDiagram(diagram: UmlDiagram) {
    const confirmed = window.confirm(`Eliminar "${diagram.name}"? Esta accion no se puede deshacer.`);
    if (!confirmed) {
      return;
    }
    await umlService.deleteDiagram(diagram.id);
    setDiagrams((current) => current.filter((item) => item.id !== diagram.id));
    setOperationMessage(`Diagrama eliminado: ${diagram.name}`);
  }

  async function saveVersion() {
    await projectService.saveVersion(projectId, {
      name: `Version ${new Date().toLocaleDateString()}`,
      description: "Snapshot creado desde frontend",
      snapshot: { diagrams: diagrams.map((diagram) => diagram.id) },
    });
    setOperationMessage("Version del proyecto guardada.");
  }

  async function createFromAi(sourceType: "text" | "voice" | "image", file?: File) {
    if (!projectId || isProcessing) {
      return;
    }
    setIsProcessing(true);
    try {
      const basePrompt = sourcePrompt.trim() || "Modelo UML generado por IA local";
      const aiResult =
        sourceType === "text"
          ? await aiService.textToUml(basePrompt)
          : sourceType === "voice"
            ? await aiService.voiceToUml({ transcript: basePrompt })
            : await aiService.imageToUml({
                description: undefined,
                image_base64: file ? await fileToBase64(file) : undefined,
                file_name: file?.name,
              });
      const generated =
        sourceType === "image"
          ? await umlService.createDiagramFromAiResult({
              project_id: projectId,
              name: "UML generado por imagen",
              description: promptFromAiResult(aiResult, "Modelo UML generado desde imagen"),
              source_type: sourceType,
              result: aiResult,
            })
          : await umlService.generate({
              project_id: projectId,
              name: `UML generado por ${sourceType === "text" ? "texto" : sourceType === "voice" ? "voz" : "imagen"}`,
              prompt: promptFromAiResult(aiResult, basePrompt),
              source_type: sourceType,
            });
      setDiagrams((current) => [generated, ...current]);
      setOperationMessage(`Modelo creado con ${aiResult.engine}. Clases: ${aiResult.classes.map((item) => item.name).join(", ")}`);
    } catch {
      setOperationMessage("No se pudo generar el modelo UML desde la entrada seleccionada.");
    } finally {
      setIsProcessing(false);
    }
  }

  async function handleImageSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (file) {
      await createFromAi("image", file);
    }
  }

  async function handleXmlSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !projectId || isProcessing) {
      return;
    }
    setIsProcessing(true);
    try {
      const imported = await umlService.importXmi({
        project_id: projectId,
        name: file.name.replace(/\.[^.]+$/, "") || "Modelo importado XML",
        file_name: file.name,
        content: await fileToText(file),
      });
      setDiagrams((current) => [imported, ...current]);
      setOperationMessage(`XML importado: ${file.name}`);
      navigate(`/proyectos/${projectId}/uml/${imported.id}`);
    } catch {
      setOperationMessage("No se pudo importar el archivo XML.");
    } finally {
      setIsProcessing(false);
    }
  }

  async function importXmlFromText() {
    if (!projectId || xmiContent.trim().length === 0 || isProcessing) {
      return;
    }
    setIsProcessing(true);
    try {
      const imported = await umlService.importXmi({
        project_id: projectId,
        name: "Modelo importado XML",
        file_name: "modelo-importado.xml",
        content: xmiContent,
      });
      setDiagrams((current) => [imported, ...current]);
      setXmiContent("");
      setOperationMessage("XML pegado importado correctamente.");
      navigate(`/proyectos/${projectId}/uml/${imported.id}`);
    } catch {
      setOperationMessage("No se pudo importar el contenido XML.");
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <section className="collab-workspace min-h-[calc(100vh-5rem)] rounded-none p-6 lg:p-8">
      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <nav className="collab-breadcrumb mb-3 flex flex-wrap items-center gap-2 text-xs font-semibold">
            <Link to="/proyectos">Proyectos</Link>
            <ChevronRight size={14} aria-hidden="true" />
            <Link to={`/proyectos/${projectId}`}>{activeProject?.name ?? "Proyecto"}</Link>
            <ChevronRight size={14} aria-hidden="true" />
            <span>Colaborativo</span>
          </nav>
          <div className="flex items-start gap-4">
            <div className="collab-icon h-12 w-12">
              <Users size={28} aria-hidden="true" />
            </div>
            <div>
              <h1 className="collab-title text-3xl font-black tracking-normal">{activeProject?.name ?? "Proyecto"}</h1>
              <p className="collab-muted mt-1 text-sm">Modo colaborativo: diagramas UML, IA, XML y versiones.</p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className={cn(buttonBase, "collab-btn-secondary h-12 px-5")} to={`/proyectos/${projectId}`}>
            <Settings size={18} aria-hidden="true" />
            Gestion
          </Link>
          <button className={cn(buttonBase, "collab-btn-primary h-12 px-6")} onClick={saveVersion} type="button">
            <Save size={18} aria-hidden="true" />
            Guardar version
          </button>
        </div>
      </div>

      <div className="collab-grid">
        <aside className="grid content-start gap-4">
          <section className="collab-card p-5">
            <div className="mb-4 flex items-start gap-3">
              <div className="collab-icon h-10 w-10">
                <FolderTree size={22} aria-hidden="true" />
              </div>
              <div>
                <h2 className="collab-title text-lg font-black">Diagramas</h2>
                <p className="collab-muted mt-1 text-sm">Crea un nuevo diagrama UML.</p>
              </div>
            </div>
            <form className="grid gap-3" onSubmit={createDiagram}>
              <label className="grid gap-2 text-sm font-bold">
                <span className="collab-title">Nombre del diagrama</span>
                <input className={inputClass} value={diagramName} onChange={(event) => setDiagramName(event.target.value)} />
              </label>
              <button className={cn(buttonBase, "collab-btn-primary w-full")} disabled={isProcessing} type="submit">
                <PlusCircle size={18} aria-hidden="true" />
                Crear diagrama
              </button>
            </form>
          </section>

          <section className="collab-card p-5">
            <div className="mb-4 flex items-start gap-3">
              <div className="collab-icon h-10 w-10">
                <Sparkles size={22} aria-hidden="true" />
              </div>
              <div>
                <h2 className="collab-title text-lg font-black">Crear desde IA</h2>
                <p className="collab-muted mt-1 text-sm">Describe el modelo que deseas generar.</p>
              </div>
            </div>
            <label className="grid gap-2 text-sm font-bold">
              <span className="collab-title">Prompt</span>
              <textarea
                className={cn(textareaClass, "min-h-28")}
                maxLength={500}
                placeholder="Ej. Sistema de ventas con clientes, productos, pedidos y pagos."
                value={sourcePrompt}
                onChange={(event) => setSourcePrompt(event.target.value)}
              />
            </label>
            <p className="collab-muted mt-1 text-right text-xs">{sourcePrompt.length}/500</p>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <button className={cn(buttonBase, "collab-btn-secondary px-2")} disabled={isProcessing} onClick={() => createFromAi("text")} type="button">
                <FileText size={16} aria-hidden="true" />
                Texto
              </button>
              <button className={cn(buttonBase, "collab-btn-secondary px-2")} disabled={isProcessing} onClick={() => createFromAi("voice")} type="button">
                <Mic size={16} aria-hidden="true" />
                Voz
              </button>
              <button
                className={cn(buttonBase, "collab-btn-secondary px-2")}
                disabled={isProcessing}
                onClick={() => imageInputRef.current?.click()}
                type="button"
              >
                <Image size={16} aria-hidden="true" />
                Imagen
              </button>
            </div>
            <button className={cn(buttonBase, "collab-btn-outline mt-3 w-full")} disabled={isProcessing} onClick={() => createFromAi("text")} type="button">
              <Sparkles size={16} aria-hidden="true" />
              Generar modelo con IA
            </button>
            <input ref={imageInputRef} className="hidden" type="file" accept="image/*" onChange={handleImageSelected} />
            <p className="collab-muted mt-3 text-xs leading-5">{operationMessage}</p>
          </section>

          <section className="collab-card p-5">
            <div className="mb-4 flex items-start gap-3">
              <div className="collab-icon h-10 w-10">
                <Upload size={22} aria-hidden="true" />
              </div>
              <div>
                <h2 className="collab-title text-lg font-black">Importar XML</h2>
                <p className="collab-muted mt-1 text-sm">Carga un archivo XML y crea los diagramas.</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button className={cn(buttonBase, "collab-btn-secondary")} disabled={isProcessing} onClick={() => xmiInputRef.current?.click()} type="button">
                <FileUp size={16} aria-hidden="true" />
                Archivo
              </button>
              <button className={cn(buttonBase, "collab-btn-secondary")} disabled={isProcessing || xmiContent.trim().length === 0} onClick={importXmlFromText} type="button">
                Importar
              </button>
            </div>
            <input ref={xmiInputRef} className="hidden" type="file" accept=".xml,text/xml,application/xml" onChange={handleXmlSelected} />
            <label className="mt-3 grid gap-2 text-sm font-bold">
              <span className="collab-title">Contenido XML</span>
              <textarea
                className={textareaClass}
                placeholder='<?xml version="1.0" encoding="windows-1252"?>'
                value={xmiContent}
                onChange={(event) => setXmiContent(event.target.value)}
              />
            </label>
          </section>
        </aside>

        <section className="collab-card p-5">
          <div className="mb-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
            <div className="flex items-start gap-3">
              <div className="collab-icon h-11 w-11">
                <Layers3 size={26} aria-hidden="true" />
              </div>
              <div>
                <h2 className="collab-title text-2xl font-black">Modelos disponibles</h2>
                <p className="collab-muted mt-1 text-sm">Diagramas UML del proyecto. Colabora, edita y manten versiones.</p>
              </div>
            </div>
            <div className="grid gap-2 sm:grid-cols-[minmax(220px,320px)_170px]">
              <label className="relative">
                <Search className="collab-muted pointer-events-none absolute left-3 top-1/2 -translate-y-1/2" size={18} aria-hidden="true" />
                <input
                  className={cn(inputClass, "pl-10")}
                  placeholder="Buscar diagramas..."
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                />
              </label>
              <label className="relative">
                <select className={cn(inputClass, "appearance-none pr-9")} value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
                  <option value="all">Todos los tipos</option>
                  {diagramTypes.map((type) => (
                    <option key={type} value={type}>
                      {diagramTypeLabel(type)}
                    </option>
                  ))}
                </select>
                <ChevronDown className="collab-muted pointer-events-none absolute right-3 top-1/2 -translate-y-1/2" size={16} aria-hidden="true" />
              </label>
            </div>
          </div>

          <div className="grid gap-3">
            {filteredDiagrams.map((diagram) => (
              <article className="collab-model-card grid gap-4 p-4 lg:grid-cols-[80px_1fr_auto]" key={diagram.id}>
                <div className="collab-model-icon">
                  <FolderTree size={38} aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="collab-title truncate text-xl font-black">{diagram.name}</h3>
                    <span className={statusClassName(diagram.status)}>{statusLabel(diagram.status)}</span>
                  </div>
                  <p className="collab-muted mt-1 line-clamp-2 text-sm">{diagram.description ?? "Diagrama UML sin descripcion."}</p>
                  <div className="mt-3 flex flex-wrap gap-2 text-xs font-bold">
                    <span className="collab-chip collab-chip-blue">{diagramTypeLabel(diagram.diagram_type)}</span>
                    <span className="collab-chip">v{diagram.current_version}</span>
                    <span className="collab-chip">
                      <CalendarDays size={14} aria-hidden="true" />
                      Creado: {formatDate(diagram.created_at)}
                    </span>
                  </div>
                </div>
                <div className="flex flex-col justify-between gap-4 lg:min-w-72">
                  <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                    <span className="collab-avatar">{memberInitial(diagram.created_by_user_id)}</span>
                    {members.length > 1 ? <span className="collab-avatar collab-avatar-muted">+{members.length - 1}</span> : null}
                  </div>
                  <div className="flex flex-wrap gap-2 lg:justify-end">
                    <Link className={cn(buttonBase, "collab-btn-primary min-w-32")} to={`/proyectos/${projectId}/uml/${diagram.id}`}>
                      <Pencil size={16} aria-hidden="true" />
                      Editar
                    </Link>
                    <button className={cn(buttonBase, "collab-btn-danger min-w-32")} onClick={() => deleteDiagram(diagram)} type="button">
                      <Trash2 size={16} aria-hidden="true" />
                      Eliminar
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {filteredDiagrams.length === 0 ? (
            <div className="collab-empty mt-6 flex min-h-64 flex-col items-center justify-center px-6 py-10 text-center">
              <FolderTree className="collab-muted mb-4" size={70} aria-hidden="true" />
              <p className="collab-title text-base font-black">No hay diagramas para mostrar.</p>
              <p className="collab-muted mt-1 max-w-md text-sm">Crea, importa o genera diagramas para visualizarlos aqui.</p>
            </div>
          ) : null}
        </section>
      </div>
    </section>
  );
}
