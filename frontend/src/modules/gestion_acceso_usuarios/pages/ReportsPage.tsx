import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Code2,
  FileCode2,
  FolderKanban,
  GitBranch,
  Layers3,
  Users
} from "lucide-react";

import { projectService } from "../../gestion_proyectos_colaboracion/services/projectService";
import type { Project, ProjectMember } from "../../gestion_proyectos_colaboracion/types/project";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import type { UmlDiagram } from "../../modelado_uml_inteligente/types/uml";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";

type ProjectReport = {
  project: Project;
  diagrams: UmlDiagram[];
  members: ProjectMember[];
};

const reportTypes = [
  {
    title: "Modelado UML",
    description: "Clases, relaciones, metodos, atributos, multiplicidades e importaciones/exportaciones XML.",
    icon: Layers3
  },
  {
    title: "Colaboracion",
    description: "Miembros por proyecto, roles, actividad colaborativa y snapshots de version.",
    icon: Users
  },
  {
    title: "Generacion",
    description: "Transformaciones UML, backend Spring Boot, frontend Flutter y artefactos descargables.",
    icon: Code2
  },
  {
    title: "Calidad",
    description: "Validaciones UML, advertencias, recomendaciones y preparacion para Enterprise Architect.",
    icon: CheckCircle2
  }
];

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es", { dateStyle: "medium" }).format(new Date(value));
}

export function ReportsPage() {
  const [reports, setReports] = useState<ProjectReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    async function loadReports() {
      setIsLoading(true);
      setError("");
      try {
        const projects = await projectService.list();
        const details = await Promise.all(
          projects.map(async (project) => {
            const [diagrams, members] = await Promise.all([
              umlService.listDiagrams(project.id).catch(() => []),
              projectService.members(project.id).catch(() => [])
            ]);
            return { project, diagrams, members };
          })
        );
        if (isMounted) {
          setReports(details);
        }
      } catch (reportError) {
        if (isMounted) {
          setError(reportError instanceof Error ? reportError.message : "No se pudieron cargar los reportes.");
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    void loadReports();
    return () => {
      isMounted = false;
    };
  }, []);

  const summary = useMemo(() => {
    const totalProjects = reports.length;
    const activeProjects = reports.filter((item) => item.project.status === "active").length;
    const totalDiagrams = reports.reduce((total, item) => total + item.diagrams.length, 0);
    const totalMembers = reports.reduce((total, item) => total + item.members.length, 0);
    const projectsWithDiagrams = reports.filter((item) => item.diagrams.length > 0).length;
    return {
      totalProjects,
      activeProjects,
      totalDiagrams,
      totalMembers,
      projectsWithDiagrams,
      averageDiagrams: totalProjects > 0 ? (totalDiagrams / totalProjects).toFixed(1) : "0"
    };
  }, [reports]);

  const metrics = [
    { label: "Proyectos activos", value: String(summary.activeProjects), icon: FolderKanban },
    { label: "Diagramas UML", value: String(summary.totalDiagrams), icon: BarChart3 },
    { label: "Colaboradores", value: String(summary.totalMembers), icon: Users },
    { label: "Promedio diagramas/proyecto", value: summary.averageDiagrams, icon: Activity }
  ];

  return (
    <section className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Reportes</h1>
        <p className="text-sm text-slate-500">
          Indicadores de proyectos, modelos UML, colaboracion y preparacion para generacion de software.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Panel key={metric.label} className="p-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-accent">
                <Icon size={20} aria-hidden="true" />
              </div>
              <p className="mt-4 text-2xl font-semibold">{isLoading ? "..." : metric.value}</p>
              <p className="text-sm text-slate-500">{metric.label}</p>
            </Panel>
          );
        })}
      </div>

      {error && (
        <Panel className="border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </Panel>
      )}

      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.9fr]">
        <Panel className="p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Estado por proyecto</h2>
              <p className="text-sm text-slate-500">Cobertura de diagramas y colaboracion.</p>
            </div>
            <StatusBadge tone="neutral">{`${summary.projectsWithDiagrams} con UML`}</StatusBadge>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-separate border-spacing-y-2 text-left text-sm">
              <thead className="text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-2">Proyecto</th>
                  <th className="px-3 py-2">Estado</th>
                  <th className="px-3 py-2">Diagramas</th>
                  <th className="px-3 py-2">Colaboradores</th>
                  <th className="px-3 py-2">Creado</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((item) => (
                  <tr className="rounded-md bg-white shadow-sm shadow-slate-200/60 dark:bg-slate-900" key={item.project.id}>
                    <td className="px-3 py-3 font-semibold text-ink dark:text-slate-100">{item.project.name}</td>
                    <td className="px-3 py-3">
                      <StatusBadge tone={item.project.status === "active" ? "success" : "neutral"}>{item.project.status}</StatusBadge>
                    </td>
                    <td className="px-3 py-3">{item.diagrams.length}</td>
                    <td className="px-3 py-3">{item.members.length}</td>
                    <td className="px-3 py-3 text-slate-500">{formatDate(item.project.created_at)}</td>
                  </tr>
                ))}
                {!isLoading && reports.length === 0 && (
                  <tr>
                    <td className="px-3 py-6 text-center text-slate-500" colSpan={5}>
                      Todavia no hay proyectos para reportar.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel className="p-5">
          <h2 className="text-lg font-semibold">Reportes esperados en CASE</h2>
          <div className="mt-4 grid gap-3">
            {reportTypes.map((item) => {
              const Icon = item.icon;
              return (
                <div className="flex gap-3 rounded-md border border-slate-200 p-3 dark:border-slate-700" key={item.title}>
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-teal-50 text-accent">
                    <Icon size={18} aria-hidden="true" />
                  </div>
                  <div>
                    <p className="font-semibold">{item.title}</p>
                    <p className="text-sm text-slate-500">{item.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Panel className="p-5">
          <GitBranch className="text-accent" size={22} aria-hidden="true" />
          <h2 className="mt-3 text-base font-semibold">Versiones y trazabilidad</h2>
          <p className="mt-2 text-sm text-slate-500">
            Reporta snapshots manuales del proyecto, cambios relevantes y estado de colaboracion.
          </p>
        </Panel>
        <Panel className="p-5">
          <FileCode2 className="text-accent" size={22} aria-hidden="true" />
          <h2 className="mt-3 text-base font-semibold">Compatibilidad XML/XMI</h2>
          <p className="mt-2 text-sm text-slate-500">
            Debe indicar importaciones y exportaciones hacia Enterprise Architect y posibles observaciones.
          </p>
        </Panel>
        <Panel className="p-5">
          <Code2 className="text-accent" size={22} aria-hidden="true" />
          <h2 className="mt-3 text-base font-semibold">Generacion de software</h2>
          <p className="mt-2 text-sm text-slate-500">
            Idealmente muestra transformaciones, backend Spring Boot, frontend Flutter y descargas producidas.
          </p>
        </Panel>
      </div>
    </section>
  );
}
