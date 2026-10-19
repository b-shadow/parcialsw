import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  Archive, BriefcaseBusiness, CalendarDays, ChevronRight, ExternalLink,
  FolderKanban, Lightbulb, List, LockKeyhole, Save, Search, Settings,
  Trash2, UserPlus, Users
} from "lucide-react";

import { useAuthStore } from "../../../core/auth/authStore";
import { Button } from "../../../shared/components/Button";
import { Panel } from "../../../shared/components/Panel";
import { projectService } from "../services/projectService";
import { useProjectStore } from "../store/projectStore";
import type { ProjectMember, ProjectMemberCandidate } from "../types/project";

const fieldClassName = "h-12 w-full rounded-md border border-slate-300 bg-white text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-accent focus:ring-2 focus:ring-teal-100 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:border-teal-500 dark:focus:ring-teal-900";

function memberInitial(member: ProjectMember) {
  const source = member.full_name?.trim() || member.email?.trim() || "U";
  return source.charAt(0).toUpperCase();
}

function formatJoinedAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { date: "Sin fecha", time: "" };
  return {
    date: new Intl.DateTimeFormat("es-BO", { day: "2-digit", month: "short", year: "numeric" }).format(date),
    time: new Intl.DateTimeFormat("es-BO", { hour: "2-digit", minute: "2-digit", hour12: false }).format(date)
  };
}

export function ProjectManagementPage() {
  const { projectId = "" } = useParams();
  const activeProject = useProjectStore((state) => state.activeProject);
  const setActiveProject = useProjectStore((state) => state.setActiveProject);
  const currentUser = useAuthStore((state) => state.user);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [candidates, setCandidates] = useState<ProjectMemberCandidate[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedRole, setSelectedRole] = useState<"ORGANIZADOR" | "EDITOR">("EDITOR");
  const [message, setMessage] = useState("");

  const availableUsers = useMemo(
    () => candidates.filter((user) => !members.some((member) => member.user_id === user.id)),
    [candidates, members]
  );
  const canManage = Boolean(
    activeProject?.owner_id === currentUser?.id
      || members.some((member) => member.user_id === currentUser?.id && member.project_role === "ORGANIZADOR")
  );

  async function loadProjectContext() {
    if (!projectId) return;
    const [project, projectMembers] = await Promise.all([
      projectService.get(projectId),
      projectService.members(projectId)
    ]);
    const isOrganizer = project.owner_id === currentUser?.id || projectMembers.some(
      (member) => member.user_id === currentUser?.id && member.project_role === "ORGANIZADOR"
    );
    const projectUsers = isOrganizer ? await projectService.memberCandidates(projectId) : [];
    setActiveProject(project);
    setMembers(projectMembers);
    setCandidates(projectUsers);
    setName(project.name);
    setDescription(project.description ?? "");
    setSelectedUserId(projectUsers.find((user) => !projectMembers.some((member) => member.user_id === user.id))?.id ?? "");
  }

  useEffect(() => {
    void loadProjectContext().catch(() => setMessage("No se pudo cargar la gestión del proyecto."));
  }, [currentUser?.id, projectId]);

  async function saveProject(event: FormEvent) {
    event.preventDefault();
    const updated = await projectService.update(projectId, {
      name: name.trim(), description: description.trim() || null
    });
    setActiveProject(updated);
    setMessage("Proyecto actualizado.");
  }

  async function addMember(event: FormEvent) {
    event.preventDefault();
    if (!selectedUserId) return;
    await projectService.addMember(projectId, { user_id: selectedUserId, project_role: selectedRole });
    await loadProjectContext();
    setMessage("Colaborador agregado.");
  }

  async function updateMemberRole(member: ProjectMember, project_role: "ORGANIZADOR" | "EDITOR") {
    const updated = await projectService.updateMember(projectId, member.id, { project_role });
    setMembers((current) => current.map((item) => item.id === member.id
      ? { ...updated, full_name: updated.full_name ?? item.full_name, email: updated.email ?? item.email }
      : item));
    setMessage("Rol de colaborador actualizado.");
  }

  async function removeMember(memberId: string) {
    await projectService.removeMember(projectId, memberId);
    await loadProjectContext();
    setMessage("Colaborador quitado.");
  }

  async function archiveProject() {
    const updated = await projectService.archive(projectId);
    setActiveProject(updated);
    setMessage("Proyecto archivado.");
  }

  const projectIsActive = activeProject?.status === "active";

  return (
    <section className="grid gap-5 pb-4 text-ink dark:text-slate-100">
      <nav aria-label="Ruta de navegación" className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
        <Link className="transition hover:text-accent" to="/proyectos">Proyectos</Link>
        <ChevronRight size={16} aria-hidden="true" />
        <span>Gestionar</span>
      </nav>

      <header className="flex flex-col justify-between gap-4 xl:flex-row xl:items-center">
        <div className="flex min-w-0 items-center gap-4">
          <span className="grid size-12 shrink-0 place-items-center rounded-md bg-teal-100 text-accent dark:bg-teal-950 dark:text-teal-300">
            <FolderKanban size={28} strokeWidth={1.8} aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-slate-950 dark:text-white md:text-3xl">Gestión de proyecto</h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Administra la información general del proyecto y sus colaboradores.</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 sm:justify-end">
          {canManage && (
            <Button className="h-12 border-slate-300 px-5" icon={<Archive size={19} aria-hidden="true" />} onClick={archiveProject} variant="secondary">
              Archivar
            </Button>
          )}
          <Link className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-accent px-5 text-sm font-semibold text-white transition hover:bg-teal-800 focus:outline-none focus:ring-2 focus:ring-teal-300 dark:bg-teal-500 dark:text-slate-950 dark:hover:bg-teal-400" to={`/proyectos/${projectId}/colaborativo`}>
            <UserPlus size={19} aria-hidden="true" />
            Modo colaborativo
            <ExternalLink size={17} aria-hidden="true" />
          </Link>
        </div>
      </header>

      {message && <p className="rounded-md border border-teal-200 bg-teal-50 px-4 py-2.5 text-sm text-teal-800 dark:border-teal-900 dark:bg-teal-950 dark:text-teal-200">{message}</p>}

      <div className="grid items-start gap-5 xl:grid-cols-5">
        <Panel className="p-5 shadow-sm md:p-6 xl:col-span-2">
          <div className="mb-7 flex items-start justify-between gap-4">
            <div className="flex min-w-0 gap-3">
              <Settings className="mt-0.5 shrink-0 text-cyan-700 dark:text-cyan-400" size={27} aria-hidden="true" />
              <div>
                <h2 className="text-lg font-bold text-slate-950 dark:text-white">Información del proyecto</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Datos principales del proyecto en el sistema.</p>
              </div>
            </div>
            {activeProject && (
              <span className={`inline-flex shrink-0 items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${projectIsActive ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" : "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"}`}>
                <span className={`size-2 rounded-full ${projectIsActive ? "bg-emerald-500" : "bg-amber-500"}`} />
                {projectIsActive ? "Activo" : "Archivado"}
              </span>
            )}
          </div>

          <form className="grid gap-5" onSubmit={saveProject}>
            <label className="grid gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200">
              <span>Nombre del proyecto <span className="text-rose-500">*</span></span>
              <span className="relative block">
                <BriefcaseBusiness className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} aria-hidden="true" />
                <input className={`${fieldClassName} pl-12 pr-4`} disabled={!canManage} required value={name} onChange={(event) => setName(event.target.value)} />
              </span>
            </label>
            <label className="grid gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200">
              Descripción
              <span className="relative block">
                <List className="pointer-events-none absolute left-4 top-4 text-slate-400" size={19} aria-hidden="true" />
                <textarea className={`${fieldClassName} min-h-36 resize-y py-3 pl-12 pr-4 leading-6`} disabled={!canManage} value={description} onChange={(event) => setDescription(event.target.value)} />
              </span>
            </label>
            <Button className="h-12 w-full text-base font-semibold" disabled={!canManage || !name.trim()} icon={<Save size={19} aria-hidden="true" />} type="submit">
              Guardar cambios
            </Button>
          </form>
        </Panel>

        <div className="grid min-w-0 gap-5 xl:col-span-3">
          {canManage && (
            <Panel className="p-5 shadow-sm md:p-6">
              <div className="mb-5 flex gap-3">
                <UserPlus className="mt-0.5 shrink-0 text-cyan-700 dark:text-cyan-400" size={28} aria-hidden="true" />
                <div>
                  <h2 className="text-lg font-bold text-slate-950 dark:text-white">Agregar colaborador</h2>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Invita usuarios al proyecto asignando un rol.</p>
                </div>
              </div>
              <form className="grid gap-4 rounded-md bg-teal-50 p-4 dark:bg-teal-950/40 lg:grid-cols-12 lg:items-end" onSubmit={addMember}>
                <label className="grid min-w-0 gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 lg:col-span-6">
                  <span>Usuario <span className="text-rose-500">*</span></span>
                  <span className="relative block">
                    <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={19} aria-hidden="true" />
                    <select className={`${fieldClassName} pl-12 pr-9`} value={selectedUserId} onChange={(event) => setSelectedUserId(event.target.value)}>
                      <option value="">Selecciona un usuario del sistema...</option>
                      {availableUsers.map((user) => <option key={user.id} value={user.id}>{user.full_name} ({user.email})</option>)}
                    </select>
                  </span>
                </label>
                <label className="grid gap-2 text-sm font-semibold text-slate-800 dark:text-slate-200 lg:col-span-3">
                  <span>Rol <span className="text-rose-500">*</span></span>
                  <select className={`${fieldClassName} px-4`} value={selectedRole} onChange={(event) => setSelectedRole(event.target.value as "ORGANIZADOR" | "EDITOR")}>
                    <option value="EDITOR">Editor</option>
                    <option value="ORGANIZADOR">Organizador</option>
                  </select>
                </label>
                <Button className="h-12 px-5 font-semibold lg:col-span-3" disabled={!selectedUserId} icon={<UserPlus size={19} aria-hidden="true" />} type="submit">Agregar</Button>
              </form>
            </Panel>
          )}

          <Panel className="min-w-0 p-5 shadow-sm md:p-6">
            <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
              <div className="flex gap-3">
                <Users className="mt-0.5 shrink-0 text-cyan-700 dark:text-cyan-400" size={28} aria-hidden="true" />
                <div>
                  <h2 className="text-lg font-bold text-slate-950 dark:text-white">Colaboradores del proyecto</h2>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Usuarios con acceso al proyecto y sus roles.</p>
                </div>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full bg-teal-100 px-3 py-1.5 text-xs font-semibold text-teal-700 dark:bg-teal-950 dark:text-teal-300">
                <Users size={14} aria-hidden="true" />
                {members.length} {members.length === 1 ? "colaborador" : "colaboradores"}
              </span>
            </div>

            <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-700">
              <div className="hidden grid-cols-12 gap-4 bg-slate-50 px-5 py-3 text-xs font-semibold text-slate-500 dark:bg-slate-800 dark:text-slate-300 md:grid">
                <span className="col-span-4">Usuario</span><span className="col-span-2">Rol</span><span className="col-span-3">Fecha de incorporación</span><span className="col-span-3">Acciones</span>
              </div>
              {members.length === 0 && <p className="px-5 py-8 text-center text-sm text-slate-500 dark:text-slate-400">No hay colaboradores en este proyecto.</p>}
              {members.map((member) => {
                const joinedAt = formatJoinedAt(member.joined_at);
                const isOwner = activeProject?.owner_id === member.user_id;
                return (
                  <div className="grid gap-4 border-t border-slate-200 p-4 first:border-t-0 dark:border-slate-700 md:grid-cols-12 md:items-center md:px-5" key={member.id}>
                    <div className="flex min-w-0 items-center gap-3 md:col-span-4">
                      <span className="grid size-11 shrink-0 place-items-center rounded-full bg-blue-100 font-bold text-blue-700 dark:bg-blue-950 dark:text-blue-300">{memberInitial(member)}</span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">{member.full_name ?? "Usuario del proyecto"}</p>
                        <p className="truncate text-xs text-slate-500 dark:text-slate-400">{member.email ?? member.user_id}</p>
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <span className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400 md:hidden">Rol</span>
                      {canManage && !isOwner ? (
                        <select aria-label={`Rol de ${member.full_name ?? member.email ?? "colaborador"}`} className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 text-xs font-semibold text-slate-700 outline-none focus:border-accent focus:ring-2 focus:ring-teal-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200" value={member.project_role} onChange={(event) => updateMemberRole(member, event.target.value as "ORGANIZADOR" | "EDITOR")}>
                          <option value="ORGANIZADOR">Organizador</option><option value="EDITOR">Editor</option>
                        </select>
                      ) : (
                        <span className="inline-flex rounded-full bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">{member.project_role === "ORGANIZADOR" ? "Organizador" : "Editor"}</span>
                      )}
                    </div>
                    <div className="md:col-span-3">
                      <span className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400 md:hidden">Fecha de incorporación</span>
                      <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                        <CalendarDays className="shrink-0 text-slate-400" size={18} aria-hidden="true" />
                        <span><span className="block">{joinedAt.date}</span>{joinedAt.time && <span className="block text-xs text-slate-400">{joinedAt.time}</span>}</span>
                      </div>
                    </div>
                    <div className="md:col-span-3">
                      <span className="mb-1 block text-xs font-semibold text-slate-500 dark:text-slate-400 md:hidden">Acciones</span>
                      {canManage && !isOwner ? (
                        <button className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-rose-300 px-3 text-xs font-semibold text-rose-600 transition hover:bg-rose-50 focus:outline-none focus:ring-2 focus:ring-rose-200 dark:border-rose-800 dark:text-rose-300 dark:hover:bg-rose-950" onClick={() => removeMember(member.id)} type="button">
                          <Trash2 size={16} aria-hidden="true" />Quitar
                        </button>
                      ) : isOwner ? (
                        <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400" title="El propietario no puede quitarse del proyecto"><LockKeyhole size={15} aria-hidden="true" />Propietario</span>
                      ) : <span className="text-xs text-slate-400">Sin permisos</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>
      </div>

      <aside className="flex items-start gap-4 rounded-md border border-slate-200 bg-white px-5 py-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <span className="grid size-11 shrink-0 place-items-center rounded-full bg-amber-100 text-amber-600 dark:bg-amber-950 dark:text-amber-300"><Lightbulb size={22} aria-hidden="true" /></span>
        <div>
          <h2 className="font-semibold text-slate-900 dark:text-white">Consejo</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Puedes agregar varios colaboradores y asignar sus responsabilidades mediante los roles del proyecto.</p>
        </div>
      </aside>
    </section>
  );
}
