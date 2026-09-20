import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Archive, ExternalLink, Save, Trash2, UserPlus, Users } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { Textarea } from "../../../shared/components/Textarea";
import { userService } from "../../gestion_acceso_usuarios/services/userService";
import type { User } from "../../gestion_acceso_usuarios/types/user";
import { projectService } from "../services/projectService";
import { useProjectStore } from "../store/projectStore";
import type { ProjectMember } from "../types/project";

export function ProjectManagementPage() {
  const { projectId = "" } = useParams();
  const activeProject = useProjectStore((state) => state.activeProject);
  const setActiveProject = useProjectStore((state) => state.setActiveProject);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedRole, setSelectedRole] = useState<"ORGANIZADOR" | "EDITOR">("EDITOR");
  const [message, setMessage] = useState("");

  const userById = useMemo(() => new Map(users.map((user) => [user.id, user])), [users]);
  const availableUsers = users.filter((user) => !members.some((member) => member.user_id === user.id));

  async function loadProjectContext() {
    if (!projectId) {
      return;
    }
    const [project, projectMembers, projectUsers] = await Promise.all([
      projectService.get(projectId),
      projectService.members(projectId),
      userService.list()
    ]);
    setActiveProject(project);
    setMembers(projectMembers);
    setUsers(projectUsers);
    setName(project.name);
    setDescription(project.description ?? "");
    setSelectedUserId(projectUsers.find((user) => !projectMembers.some((member) => member.user_id === user.id))?.id ?? "");
  }

  useEffect(() => {
    void loadProjectContext().catch(() => setMessage("No se pudo cargar la gestion del proyecto."));
  }, [projectId]);

  async function saveProject(event: FormEvent) {
    event.preventDefault();
    const updated = await projectService.update(projectId, {
      name: name.trim(),
      description: description.trim() || null
    });
    setActiveProject(updated);
    setMessage("Proyecto actualizado.");
  }

  async function addMember(event: FormEvent) {
    event.preventDefault();
    if (!selectedUserId) {
      return;
    }
    await projectService.addMember(projectId, {
      user_id: selectedUserId,
      project_role: selectedRole
    });
    await loadProjectContext();
    setMessage("Colaborador agregado.");
  }

  async function updateMemberRole(member: ProjectMember, project_role: "ORGANIZADOR" | "EDITOR") {
    const updated = await projectService.updateMember(projectId, member.id, { project_role });
    setMembers((current) => current.map((item) => (item.id === member.id ? updated : item)));
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

  return (
    <section className="grid gap-5">
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div>
          <h1 className="text-2xl font-semibold">Gestion de proyecto</h1>
          <p className="mt-1 text-sm text-slate-600">{activeProject?.name ?? "Proyecto colaborativo"}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to={`/proyectos/${projectId}/colaborativo`}>
            <Button icon={<ExternalLink size={18} aria-hidden="true" />}>Modo colaborativo</Button>
          </Link>
          <Button icon={<Archive size={18} aria-hidden="true" />} onClick={archiveProject} variant="ghost">
            Archivar
          </Button>
        </div>
      </div>

      {message && <p className="rounded-md bg-teal-50 px-3 py-2 text-sm text-accent">{message}</p>}

      <div className="grid gap-5 lg:grid-cols-[420px_1fr]">
        <Panel className="p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Datos generales</h2>
            {activeProject && (
              <StatusBadge tone={activeProject.status === "active" ? "success" : "warning"}>{activeProject.status}</StatusBadge>
            )}
          </div>
          <form className="grid gap-3" onSubmit={saveProject}>
            <Input label="Nombre del proyecto" value={name} onChange={(event) => setName(event.target.value)} />
            <Textarea label="Descripcion" value={description} onChange={(event) => setDescription(event.target.value)} />
            <Button icon={<Save size={18} aria-hidden="true" />} type="submit">
              Guardar cambios
            </Button>
          </form>
        </Panel>

        <div className="grid gap-5">
          <Panel className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <UserPlus className="text-accent" size={20} aria-hidden="true" />
              <h2 className="text-lg font-semibold">Agregar colaborador</h2>
            </div>
            <form className="grid gap-3 md:grid-cols-[1fr_170px_auto]" onSubmit={addMember}>
              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Usuario
                <select
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
                  value={selectedUserId}
                  onChange={(event) => setSelectedUserId(event.target.value)}
                >
                  <option value="">Seleccione usuario</option>
                  {availableUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.email}
                    </option>
                  ))}
                </select>
              </label>
              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Rol
                <select
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
                  value={selectedRole}
                  onChange={(event) => setSelectedRole(event.target.value as "ORGANIZADOR" | "EDITOR")}
                >
                  <option value="EDITOR">Editor</option>
                  <option value="ORGANIZADOR">Organizador</option>
                </select>
              </label>
              <Button className="self-end" disabled={!selectedUserId} icon={<UserPlus size={18} aria-hidden="true" />} type="submit">
                Agregar
              </Button>
            </form>
          </Panel>

          <Panel className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <Users className="text-accent" size={20} aria-hidden="true" />
              <h2 className="text-lg font-semibold">Colaboradores</h2>
            </div>
            <div className="grid gap-3">
              {members.map((member) => {
                const user = userById.get(member.user_id);
                return (
                  <div className="grid gap-3 rounded-md border border-slate-200 p-4 md:grid-cols-[1fr_180px_auto]" key={member.id}>
                    <div>
                      <p className="font-semibold">{user?.full_name ?? member.user_id}</p>
                      <p className="mt-1 text-sm text-slate-600">{user?.email ?? member.user_id}</p>
                    </div>
                    <select
                      className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
                      value={member.project_role}
                      onChange={(event) => updateMemberRole(member, event.target.value as "ORGANIZADOR" | "EDITOR")}
                    >
                      <option value="ORGANIZADOR">Organizador</option>
                      <option value="EDITOR">Editor</option>
                    </select>
                    <Button icon={<Trash2 size={18} aria-hidden="true" />} onClick={() => removeMember(member.id)} variant="danger">
                      Quitar
                    </Button>
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>
      </div>
    </section>
  );
}
