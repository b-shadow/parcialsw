import { useEffect, useState } from "react";
import { Archive, FolderOpen } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "../../../shared/components/Button";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { ProjectForm } from "../components/ProjectForm";
import { projectService } from "../services/projectService";
import type { Project } from "../types/project";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");

  async function loadProjects() {
    try {
      setProjects(await projectService.list());
      setError("");
    } catch {
      setError("No se pudieron cargar los proyectos.");
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  return (
    <section className="grid gap-5">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="text-2xl font-semibold">Proyectos colaborativos</h1>
          <p className="mt-1 text-sm text-slate-600">Gestion de proyectos, versiones e integrantes.</p>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[360px_1fr]">
        <Panel className="p-5">
          <h2 className="mb-4 text-lg font-semibold">Nuevo proyecto</h2>
          <ProjectForm onCreate={async (payload) => {
            await projectService.create(payload);
            await loadProjects();
          }} />
        </Panel>

        <div className="grid gap-3">
          {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          {projects.map((project) => (
            <Panel className="p-4" key={project.id}>
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold">{project.name}</h2>
                    <StatusBadge tone={project.status === "active" ? "success" : "warning"}>{project.status}</StatusBadge>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{project.description ?? "Proyecto sin descripcion"}</p>
                </div>
                <div className="flex gap-2">
                  <Link to={`/proyectos/${project.id}`}>
                    <Button icon={<FolderOpen size={18} aria-hidden="true" />} variant="secondary">
                      Abrir
                    </Button>
                  </Link>
                  <Button
                    icon={<Archive size={18} aria-hidden="true" />}
                    variant="ghost"
                    onClick={async () => {
                      await projectService.archive(project.id);
                      await loadProjects();
                    }}
                  >
                    Archivar
                  </Button>
                </div>
              </div>
            </Panel>
          ))}
          {projects.length === 0 && !error && (
            <Panel className="p-8 text-center text-sm text-slate-600">No hay proyectos cargados.</Panel>
          )}
        </div>
      </div>
    </section>
  );
}
