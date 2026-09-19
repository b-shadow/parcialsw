import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { GitBranch, Network, Save, Users } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { useProjectStore } from "../store/projectStore";
import { projectService } from "../services/projectService";
import type { ProjectMember } from "../types/project";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import type { UmlDiagram } from "../../modelado_uml_inteligente/types/uml";

export function ProjectWorkspacePage() {
  const { projectId = "" } = useParams();
  const activeProject = useProjectStore((state) => state.activeProject);
  const setActiveProject = useProjectStore((state) => state.setActiveProject);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [diagrams, setDiagrams] = useState<UmlDiagram[]>([]);
  const [diagramName, setDiagramName] = useState("Diagrama de dominio");
  const projectReady = useMemo(() => Boolean(projectId), [projectId]);

  useEffect(() => {
    if (!projectReady) {
      return;
    }
    projectService.get(projectId).then(setActiveProject).catch(() => undefined);
    projectService.members(projectId).then(setMembers).catch(() => undefined);
    umlService.listDiagrams(projectId).then(setDiagrams).catch(() => undefined);
  }, [projectId, projectReady, setActiveProject]);

  async function createDiagram(event: FormEvent) {
    event.preventDefault();
    if (diagramName.trim().length < 2) {
      return;
    }
    const diagram = await umlService.createDiagram({
      project_id: projectId,
      name: diagramName,
      description: "Diagrama de clases principal"
    });
    setDiagrams((current) => [diagram, ...current]);
    setDiagramName("");
  }

  async function saveVersion() {
    await projectService.saveVersion(projectId, {
      name: `Version ${new Date().toLocaleDateString()}`,
      description: "Snapshot creado desde frontend",
      snapshot: { diagrams: diagrams.map((diagram) => diagram.id) }
    });
  }

  return (
    <section className="grid gap-5">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="text-2xl font-semibold">{activeProject?.name ?? "Proyecto"}</h1>
          <p className="mt-1 text-sm text-slate-600">{activeProject?.description ?? "Entorno colaborativo"}</p>
        </div>
        <Button icon={<Save size={18} aria-hidden="true" />} onClick={saveVersion}>
          Guardar version
        </Button>
      </div>

      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        <div className="grid gap-5">
          <Panel className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <Network className="text-accent" size={20} aria-hidden="true" />
              <h2 className="text-lg font-semibold">Diagramas</h2>
            </div>
            <form className="grid gap-3" onSubmit={createDiagram}>
              <Input label="Nombre" value={diagramName} onChange={(event) => setDiagramName(event.target.value)} />
              <Button type="submit">Crear diagrama</Button>
            </form>
          </Panel>
          <Panel className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <Users className="text-accent" size={20} aria-hidden="true" />
              <h2 className="text-lg font-semibold">Integrantes</h2>
            </div>
            <div className="grid gap-2">
              {members.map((member) => (
                <div className="rounded-md bg-slate-50 p-3 text-sm" key={member.id}>
                  <p className="font-medium">{member.project_role}</p>
                  <p className="text-xs text-slate-500">{member.user_id}</p>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <Panel className="p-5">
          <div className="mb-4 flex items-center gap-2">
            <GitBranch className="text-accent" size={20} aria-hidden="true" />
            <h2 className="text-lg font-semibold">Modelos disponibles</h2>
          </div>
          <div className="grid gap-3">
            {diagrams.map((diagram) => (
              <Link
                className="rounded-md border border-slate-200 p-4 transition hover:border-accent hover:bg-teal-50"
                key={diagram.id}
                to={`/proyectos/${projectId}/uml/${diagram.id}`}
              >
                <p className="font-semibold">{diagram.name}</p>
                <p className="mt-1 text-sm text-slate-600">{diagram.description ?? "Diagrama de clases"}</p>
              </Link>
            ))}
          </div>
        </Panel>
      </div>
    </section>
  );
}
