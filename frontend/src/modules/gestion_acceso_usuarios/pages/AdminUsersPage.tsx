import { useEffect, useMemo, useState } from "react";
import { RefreshCcw, Save, ShieldCheck, UserCog, Users } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import type { Role, User } from "../types/user";
import { userService } from "../services/userService";

function formatDate(value?: string | null) {
  if (!value) {
    return "Sin registro";
  }
  return new Intl.DateTimeFormat("es", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [selectedRole, setSelectedRole] = useState<Role["name"]>("EDITOR");
  const [isActive, setIsActive] = useState(true);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const selectedUser = useMemo(
    () => users.find((user) => user.id === selectedUserId),
    [selectedUserId, users]
  );

  async function load() {
    setIsLoading(true);
    setMessage("");
    try {
      const [userList, roleList] = await Promise.all([
        userService.list(),
        userService.listRoles()
      ]);
      setUsers(userList);
      setRoles(roleList);
      const first = userList[0];
      if (first) {
        setSelectedUserId(first.id);
        setSelectedRole((first.role_names[0] as Role["name"]) ?? "EDITOR");
        setIsActive(first.is_active);
      }
    } catch {
      setMessage("No se pudo cargar la administracion de usuarios.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (selectedUser) {
      setSelectedRole((selectedUser.role_names[0] as Role["name"]) ?? "EDITOR");
      setIsActive(selectedUser.is_active);
    }
  }, [selectedUser]);

  async function saveChanges() {
    if (!selectedUser) {
      return;
    }
    setIsSaving(true);
    setMessage("");
    try {
      const updated = await userService.updateUser(selectedUser.id, {
        is_active: isActive,
        role_name: selectedRole
      });
      setUsers((current) => current.map((user) => (user.id === updated.id ? updated : user)));
      setMessage("Usuario actualizado y registrado en bitacora.");
    } catch {
      setMessage("No se pudo actualizar el usuario. Verifica permisos de Administrador.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="grid gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Gestion de usuarios</h1>
          <p className="text-sm text-slate-500">Administracion global de usuarios, roles y estado de acceso.</p>
        </div>
        <Button icon={<RefreshCcw size={16} aria-hidden="true" />} onClick={load} type="button" variant="secondary">
          Actualizar
        </Button>
      </div>

      {message && <p className="rounded-md bg-slate-50 px-4 py-3 text-sm text-slate-700">{message}</p>}

      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel className="overflow-hidden">
          <div className="flex items-center gap-3 border-b border-slate-200 p-5">
            <Users className="text-accent" size={22} aria-hidden="true" />
            <div>
              <h2 className="text-lg font-semibold">Usuarios del sistema</h2>
              <p className="text-sm text-slate-500">{users.length} registros disponibles</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Usuario</th>
                  <th className="px-4 py-3">Rol</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Ultimo acceso</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((user) => (
                  <tr
                    className={user.id === selectedUserId ? "bg-teal-50/70" : "cursor-pointer hover:bg-slate-50"}
                    key={user.id}
                    onClick={() => setSelectedUserId(user.id)}
                  >
                    <td className="px-4 py-3">
                      <p className="font-semibold text-ink">{user.full_name}</p>
                      <p className="text-xs text-slate-500">{user.email}</p>
                    </td>
                    <td className="px-4 py-3">{user.role_names.join(", ") || "Sin rol"}</td>
                    <td className="px-4 py-3">
                      <StatusBadge tone={user.is_active ? "success" : "danger"}>
                        {user.is_active ? "active" : "inactive"}
                      </StatusBadge>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(user.last_access_at)}</td>
                  </tr>
                ))}
                {!isLoading && users.length === 0 && (
                  <tr>
                    <td className="px-4 py-6 text-center text-slate-500" colSpan={4}>
                      No hay usuarios registrados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel className="p-5">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-accent">
              <UserCog size={20} aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Permisos globales</h2>
              <p className="text-sm text-slate-500">Cambios restringidos al rol Administrador.</p>
            </div>
          </div>

          {selectedUser ? (
            <div className="grid gap-4">
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Usuario seleccionado</p>
                <p className="mt-1 font-semibold">{selectedUser.full_name}</p>
                <p className="text-sm text-slate-500">{selectedUser.email}</p>
              </div>

              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Rol global
                <select
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-ink outline-none focus:border-accent"
                  onChange={(event) => setSelectedRole(event.target.value as Role["name"])}
                  value={selectedRole}
                >
                  {roles.map((role) => (
                    <option key={role.id} value={role.name}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex items-center gap-3 rounded-md border border-slate-200 p-4 text-sm font-medium text-slate-700">
                <input
                  checked={isActive}
                  className="h-4 w-4 accent-teal-600"
                  onChange={(event) => setIsActive(event.target.checked)}
                  type="checkbox"
                />
                Usuario activo
              </label>

              <Button
                disabled={isSaving}
                icon={<Save size={16} aria-hidden="true" />}
                onClick={saveChanges}
                type="button"
              >
                {isSaving ? "Guardando..." : "Guardar cambios"}
              </Button>
            </div>
          ) : (
            <p className="rounded-md bg-slate-50 p-4 text-sm text-slate-500">Seleccione un usuario.</p>
          )}

          <div className="mt-5 flex items-start gap-3 rounded-md bg-slate-50 p-4 text-sm text-slate-600">
            <ShieldCheck className="mt-0.5 text-accent" size={18} aria-hidden="true" />
            <p>Todo cambio de rol o estado queda registrado automaticamente en la bitacora.</p>
          </div>
        </Panel>
      </div>
    </section>
  );
}
