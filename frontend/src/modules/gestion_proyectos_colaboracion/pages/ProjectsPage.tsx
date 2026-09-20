import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  Archive,
  BarChart3,
  Box,
  Calendar,
  Code2,
  FileText,
  Folder,
  Layers,
  Plus,
  Search,
  User,
  Users
} from "lucide-react";
import { Link } from "react-router-dom";

import { useThemeStore } from "../../../core/theme/themeStore";
import { cn } from "../../../shared/utils/cn";
import { projectService } from "../services/projectService";
import type { Project } from "../types/project";

function formatProjectDate(value: string) {
  return new Intl.DateTimeFormat("es", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(value));
}

function projectStatus(project: Project) {
  return project.status === "active"
    ? { label: "Activo", tone: "bg-teal-50 text-accent dark:bg-teal-400/10 dark:text-teal-300" }
    : { label: "Archivado", tone: "bg-amber-50 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300" };
}

export function ProjectsPage() {
  const isDark = useThemeStore((state) => state.mode === "dark");
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const [projectName, setProjectName] = useState("Sistema de ventas");
  const [projectDescription, setProjectDescription] = useState("Modelo colaborativo inicial");
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);

  const panelTone = isDark
    ? "border-[#233149] bg-[#0b1424] text-slate-100 shadow-[0_18px_54px_rgba(0,0,0,0.20)]"
    : "border-[#dfeafb] bg-white text-[#070b5f] shadow-[0_18px_54px_rgba(15,23,42,0.08)]";
  const softPanelTone = isDark ? "bg-[#111f33]" : "bg-teal-50";
  const mutedTone = isDark ? "text-slate-400" : "text-blue-700/70";
  const inputTone = isDark
    ? "border-slate-700 bg-[#08111f] text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:ring-teal-400/15"
    : "border-blue-200 bg-white text-[#070b5f] placeholder:text-blue-700/45 focus:border-accent focus:ring-teal-100";

  const activeCount = projects.filter((project) => project.status === "active").length;
  const archivedCount = projects.filter((project) => project.status !== "active").length;
  const filteredProjects = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) {
      return projects;
    }
    return projects.filter((project) =>
      [project.name, project.description ?? "", project.status].some((value) => value.toLowerCase().includes(term))
    );
  }, [projects, search]);

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

  async function createProject(event: FormEvent) {
    event.preventDefault();
    if (projectName.trim().length < 2) {
      return;
    }
    setCreating(true);
    try {
      await projectService.create({
        name: projectName.trim(),
        description: projectDescription.trim() || undefined
      });
      setProjectName("");
      setProjectDescription("");
      await loadProjects();
    } finally {
      setCreating(false);
    }
  }

  async function archiveProject(projectId: string) {
    await projectService.archive(projectId);
    await loadProjects();
  }

  return (
    <section className="grid gap-7">
      <div className="relative flex min-h-28 items-start justify-between gap-8 overflow-hidden px-1 py-2">
        <div className="relative z-10 pt-2">
          <h1 className="text-[34px] font-black leading-tight tracking-tight">Gestion de proyectos</h1>
          <p className={cn("mt-2 text-xl", mutedTone)}>Administra proyectos y generacion de codigo.</p>
        </div>
        <div className="pointer-events-none relative hidden min-h-28 w-96 shrink-0 lg:block">
          <Box className={cn("absolute right-36 top-0 h-28 w-28", isDark ? "text-teal-400/10" : "text-teal-100")} />
          <p className={cn("absolute right-0 top-7 text-right text-base font-medium leading-6", isDark ? "text-slate-500" : "text-blue-700/70")}>
            "Del modelo al codigo,
            <br />
            en equipo."
          </p>
          <div className="absolute bottom-4 right-0 h-1 w-12 rounded-full bg-accent" />
        </div>
      </div>

      <div className="projects-metrics-grid">
        {[
          { icon: Folder, value: activeCount, label: "Proyectos activos", caption: "En desarrollo" },
          { icon: Code2, value: 0, label: "Generaciones", caption: "Codigo generado" },
          { icon: Archive, value: archivedCount, label: "Archivados", caption: "Proyectos finalizados" }
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div className={cn("flex min-h-[118px] items-center gap-8 rounded-xl border px-7 py-5", panelTone)} key={item.label}>
              <div className={cn("flex h-20 w-20 shrink-0 items-center justify-center rounded-xl text-accent", softPanelTone)}>
                <Icon size={39} aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <p className="text-[28px] font-black leading-7">{item.value}</p>
                <p className="mt-1 text-xl font-black leading-6">{item.label}</p>
                <p className={cn("mt-1 text-base", mutedTone)}>{item.caption}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="projects-content-grid">
        <div className={cn("rounded-xl border p-7", panelTone)}>
          <div className="mb-5 flex items-start gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-accent text-white">
              <Plus size={30} aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-2xl font-black">Nuevo proyecto</h2>
              <p className={cn("mt-1 text-base leading-6", mutedTone)}>Crea un nuevo proyecto CASE para modelar y generar codigo.</p>
            </div>
          </div>

          <form className="grid gap-5" onSubmit={createProject}>
            <label className="grid gap-2 text-base font-bold">
              Nombre del proyecto
              <span className={cn("flex min-h-12 items-center gap-3 rounded-lg border px-4 transition focus-within:ring-4", inputTone)}>
                <FileText size={22} aria-hidden="true" />
                <input
                  className="h-11 min-w-0 flex-1 bg-transparent text-base font-semibold outline-none"
                  placeholder="Ej. Sistema de ventas"
                  value={projectName}
                  onChange={(event) => setProjectName(event.target.value)}
                />
              </span>
            </label>
            <label className="grid gap-2 text-base font-bold">
              Descripcion
              <span className={cn("flex min-h-24 gap-3 rounded-lg border px-4 py-3 transition focus-within:ring-4", inputTone)}>
                <FileText className="mt-1 shrink-0" size={22} aria-hidden="true" />
                <textarea
                  className="min-h-20 min-w-0 flex-1 resize-y bg-transparent text-base font-semibold outline-none"
                  placeholder="Describe el objetivo del proyecto..."
                  value={projectDescription}
                  onChange={(event) => setProjectDescription(event.target.value)}
                />
              </span>
            </label>
            <button
              className="inline-flex h-14 items-center justify-center gap-3 rounded-lg bg-accent px-5 text-lg font-black text-white shadow-lg shadow-teal-900/15 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={creating}
              type="submit"
            >
              <Plus size={26} aria-hidden="true" />
              {creating ? "Creando" : "Crear proyecto"}
            </button>
          </form>
        </div>

        <div className={cn("rounded-xl border p-7", panelTone)}>
          <div className="mb-7 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-start gap-4">
              <Layers className="mt-1 text-blue-900 dark:text-teal-300" size={42} aria-hidden="true" />
              <div>
                <h2 className="text-2xl font-black">Proyectos existentes</h2>
                <p className={cn("mt-1 text-base", mutedTone)}>Gestiona tus proyectos y accede a sus herramientas.</p>
              </div>
            </div>
            <label className={cn("flex h-12 w-full items-center gap-3 rounded-lg border px-4 transition focus-within:ring-4 lg:max-w-xs", inputTone)}>
              <Search size={23} aria-hidden="true" />
              <input
                className="min-w-0 flex-1 bg-transparent text-base outline-none"
                placeholder="Buscar proyectos..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
          </div>

          {error && <p className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

          <div className="grid gap-4">
            {filteredProjects.map((project, index) => {
              const status = projectStatus(project);
              const ProjectIcon = index % 2 === 0 ? BarChart3 : Code2;
              return (
                <article
                  className={cn(
                    "rounded-xl border p-5 transition",
                    isDark ? "border-slate-800 bg-[#0b1424] hover:border-teal-400/50" : "border-blue-100 bg-white hover:border-teal-300"
                  )}
                  key={project.id}
                >
                  <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
                    <div className="flex gap-5">
                      <div className={cn("flex h-20 w-20 shrink-0 items-center justify-center rounded-xl text-accent", softPanelTone)}>
                        <ProjectIcon size={42} aria-hidden="true" />
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="text-2xl font-black">{project.name}</h3>
                          <span className={cn("rounded-full px-4 py-1 text-sm font-black", status.tone)}>{status.label}</span>
                        </div>
                        <p className={cn("mt-2 max-w-3xl text-lg leading-7", mutedTone)}>
                          {project.description ?? "Proyecto CASE para modelado UML y generacion de codigo."}
                        </p>
                        <div className={cn("mt-4 flex flex-wrap items-center gap-x-8 gap-y-2 text-base", mutedTone)}>
                          <span className="inline-flex items-center gap-2">
                            <Code2 size={19} aria-hidden="true" />
                            Java / Spring Boot
                          </span>
                          <span className="inline-flex items-center gap-2">
                            <Calendar size={19} aria-hidden="true" />
                            Creado: {formatProjectDate(project.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className={cn("mt-5 h-px", isDark ? "bg-slate-800" : "bg-blue-100")} />
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <Link to={`/proyectos/${project.id}`}>
                      <button className="inline-flex h-12 w-full items-center justify-center gap-3 rounded-lg border border-accent bg-transparent px-4 text-base font-black text-accent transition hover:bg-teal-50 dark:hover:bg-teal-400/10">
                        <User size={21} aria-hidden="true" />
                        Gestionar
                      </button>
                    </Link>
                    <Link to={`/proyectos/${project.id}/colaborativo`}>
                      <button className={cn("inline-flex h-12 w-full items-center justify-center gap-3 rounded-lg border px-4 text-base font-black transition", isDark ? "border-slate-700 text-slate-200 hover:bg-slate-800" : "border-blue-200 text-blue-900 hover:bg-blue-50")}>
                        <Users size={21} aria-hidden="true" />
                        Colaborativo
                      </button>
                    </Link>
                    <button
                      className={cn("inline-flex h-12 w-full items-center justify-center gap-3 rounded-lg border px-4 text-base font-black transition", isDark ? "border-slate-700 text-slate-200 hover:bg-slate-800" : "border-blue-200 text-blue-900 hover:bg-blue-50")}
                      disabled={project.status !== "active"}
                      onClick={() => archiveProject(project.id)}
                      type="button"
                    >
                      <Archive size={21} aria-hidden="true" />
                      {project.status === "active" ? "Archivar" : "Archivado"}
                    </button>
                  </div>
                </article>
              );
            })}
            {filteredProjects.length === 0 && !error && (
              <div className={cn("rounded-xl border p-10 text-center text-base", isDark ? "border-slate-800 text-slate-400" : "border-blue-100 text-blue-700/70")}>
                No hay proyectos para mostrar.
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
