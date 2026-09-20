import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, Code2, Database, Download, FolderKanban, Smartphone } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { projectService } from "../../gestion_proyectos_colaboracion/services/projectService";
import type { Project } from "../../gestion_proyectos_colaboracion/types/project";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import type { UmlDiagram } from "../../modelado_uml_inteligente/types/uml";
import { generationService } from "../services/generationService";
import type { GeneratedBackend, GeneratedFrontend, Transformation } from "../types/generation";

type LoadingKey = "projects" | "diagrams" | "transform" | "backend" | "frontend" | "";

export function GenerationPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [diagrams, setDiagrams] = useState<UmlDiagram[]>([]);
  const [projectId, setProjectId] = useState("");
  const [diagramId, setDiagramId] = useState("");
  const [name, setName] = useState("AplicacionGenerada");
  const [transformation, setTransformation] = useState<Transformation | null>(null);
  const [backend, setBackend] = useState<GeneratedBackend | null>(null);
  const [frontend, setFrontend] = useState<GeneratedFrontend | null>(null);
  const [loading, setLoading] = useState<LoadingKey>("projects");
  const [error, setError] = useState("");

  const selectedProject = useMemo(() => projects.find((project) => project.id === projectId), [projectId, projects]);
  const selectedDiagram = useMemo(() => diagrams.find((diagram) => diagram.id === diagramId), [diagramId, diagrams]);

  useEffect(() => {
    async function loadProjects() {
      setLoading("projects");
      setError("");
      try {
        const result = await projectService.list();
        setProjects(result);
      } catch {
        setError("No se pudieron cargar los proyectos.");
      } finally {
        setLoading("");
      }
    }

    void loadProjects();
  }, []);

  useEffect(() => {
    async function loadDiagrams() {
      if (!projectId) {
        setDiagrams([]);
        setDiagramId("");
        resetPipeline();
        return;
      }
      setLoading("diagrams");
      setError("");
      setDiagramId("");
      resetPipeline();
      try {
        const result = await umlService.listDiagrams(projectId);
        setDiagrams(result);
      } catch {
        setError("No se pudieron cargar los diagramas del proyecto.");
      } finally {
        setLoading("");
      }
    }

    void loadDiagrams();
  }, [projectId]);

  function resetPipeline() {
    setTransformation(null);
    setBackend(null);
    setFrontend(null);
  }

  function handleDiagramChange(value: string) {
    setDiagramId(value);
    resetPipeline();
  }

  async function handleTransform() {
    if (!diagramId) {
      setError("Seleccione un diagrama UML del proyecto.");
      return;
    }
    setLoading("transform");
    setError("");
    setBackend(null);
    setFrontend(null);
    try {
      const created = await generationService.transform({ diagram_id: diagramId, target_platform: "full_stack" });
      setTransformation(created);
    } catch {
      setError("No se pudo transformar el modelo UML seleccionado.");
    } finally {
      setLoading("");
    }
  }

  async function generateBackend() {
    if (!transformation) {
      return;
    }
    setLoading("backend");
    setError("");
    setFrontend(null);
    try {
      const generated = await generationService.springBoot({
        transformation_id: transformation.id,
        name: `${name}Backend`,
        version_label: "v1"
      });
      setBackend(generated);
    } catch {
      setError("No se pudo generar el backend Spring Boot.");
    } finally {
      setLoading("");
    }
  }

  async function generateFrontend() {
    if (!transformation || !backend) {
      return;
    }
    setLoading("frontend");
    setError("");
    try {
      const generated = await generationService.flutter({
        transformation_id: transformation.id,
        name: `${name}Mobile`,
        version_label: "v1",
        backend_id: backend.id
      });
      setFrontend(generated);
    } catch {
      setError("No se pudo generar el frontend Flutter.");
    } finally {
      setLoading("");
    }
  }

  async function downloadBackend() {
    if (!backend) {
      return;
    }
    const blob = await generationService.downloadSpringBoot(backend.id);
    downloadBlob(blob, `${backend.name}.zip`);
  }

  async function downloadFrontend() {
    if (!frontend) {
      return;
    }
    const blob = await generationService.downloadFlutter(frontend.id);
    downloadBlob(blob, `${frontend.name}.zip`);
  }

  function downloadBlob(blob: Blob, fileName: string) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Transformacion y generacion</h1>
        <p className="mt-1 text-sm text-slate-600">Seleccione proyecto y diagrama para generar Spring Boot y Flutter.</p>
      </div>

      {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
        <Panel className="p-5">
          <div className="grid gap-4">
            <label className="grid gap-1 text-sm font-medium text-slate-700">
              Proyecto
              <select
                className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                disabled={loading === "projects"}
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              >
                <option value="">Seleccione un proyecto</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm font-medium text-slate-700">
              Diagrama UML
              <select
                className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                disabled={!projectId || loading === "diagrams"}
                value={diagramId}
                onChange={(event) => handleDiagramChange(event.target.value)}
              >
                <option value="">{projectId ? "Seleccione un diagrama" : "Primero seleccione proyecto"}</option>
                {diagrams.map((diagram) => (
                  <option key={diagram.id} value={diagram.id}>
                    {diagram.name}
                  </option>
                ))}
              </select>
            </label>

            <Input label="Nombre base" value={name} onChange={(event) => setName(event.target.value)} />

            <Button disabled={!diagramId || loading === "transform"} icon={<BrainCircuit size={18} aria-hidden="true" />} onClick={handleTransform}>
              {loading === "transform" ? "Transformando" : "Transformar UML"}
            </Button>
          </div>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Panel className="p-5">
            <FolderKanban className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Seleccion</h2>
            <p className="mt-2 text-sm text-slate-600">{selectedProject?.name ?? "Proyecto pendiente"}</p>
            <p className="mt-1 text-sm text-slate-500">{selectedDiagram?.name ?? "Diagrama pendiente"}</p>
          </Panel>

          <Panel className="p-5">
            <Database className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Modelo intermedio</h2>
            <p className="mt-2 break-all text-sm text-slate-600">{transformation?.id ?? "Sin transformacion activa"}</p>
            <div className="mt-4">
              <StatusBadge tone={transformation ? "success" : "neutral"}>{transformation?.status ?? "pendiente"}</StatusBadge>
            </div>
          </Panel>

          <Panel className="p-5">
            <Code2 className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Spring Boot</h2>
            <p className="mt-2 text-sm text-slate-600">{backend?.name ?? "Disponible despues de transformar"}</p>
            {backend && (
              <p className="mt-2 text-xs text-slate-500">
                {backend.manifest.file_count ?? 0} archivos, PostgreSQL {String(backend.manifest.database_name ?? "")}
              </p>
            )}
            <Button className="mt-4" disabled={!transformation || loading === "backend"} onClick={generateBackend} variant="secondary">
              {loading === "backend" ? "Generando" : "Generar backend"}
            </Button>
            <Button className="mt-2 w-full" disabled={!backend} icon={<Download size={18} aria-hidden="true" />} onClick={downloadBackend} variant="ghost">
              Descargar ZIP
            </Button>
          </Panel>

          <Panel className="p-5">
            <Smartphone className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Flutter</h2>
            <p className="mt-2 text-sm text-slate-600">{frontend?.name ?? (backend ? "Disponible" : "Genere backend primero")}</p>
            {frontend && (
              <p className="mt-2 text-xs text-slate-500">
                {frontend.manifest.file_count ?? 0} archivos, API {String(frontend.manifest.api_base_url ?? "")}
              </p>
            )}
            <Button className="mt-4" disabled={!backend || loading === "frontend"} onClick={generateFrontend} variant="secondary">
              {loading === "frontend" ? "Generando" : "Generar frontend"}
            </Button>
            <Button className="mt-2 w-full" disabled={!frontend} icon={<Download size={18} aria-hidden="true" />} onClick={downloadFrontend} variant="ghost">
              Descargar ZIP
            </Button>
          </Panel>
        </div>
      </div>
    </section>
  );
}
