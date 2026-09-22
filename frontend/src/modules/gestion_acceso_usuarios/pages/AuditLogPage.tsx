import { FormEvent, useEffect, useMemo, useState } from "react";
import { ClipboardList, Filter, RefreshCcw } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import type { AuditLog, User } from "../types/user";
import { userService } from "../services/userService";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("es", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function metadataPreview(value: Record<string, unknown>) {
  const text = JSON.stringify(value);
  return text === "{}" ? "Sin metadatos" : text;
}

export function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [moduleFilter, setModuleFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const usersById = useMemo(() => new Map(users.map((user) => [user.id, user])), [users]);

  async function load(params?: { module?: string; action?: string; user_id?: string }) {
    setIsLoading(true);
    setMessage("");
    try {
      const [logList, userList] = await Promise.all([
        userService.listAuditLogs({ ...params, limit: 150 }),
        userService.list()
      ]);
      setLogs(logList);
      setUsers(userList);
    } catch {
      setMessage("No se pudo cargar la bitacora. Verifica permisos de Administrador.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    load({
      module: moduleFilter.trim() || undefined,
      action: actionFilter.trim() || undefined,
      user_id: userFilter || undefined
    });
  }

  return (
    <section className="grid gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Bitacora del sistema</h1>
          <p className="text-sm text-slate-500">Seguimiento de acciones, usuarios, resultados y metadatos operativos.</p>
        </div>
        <Button icon={<RefreshCcw size={16} aria-hidden="true" />} onClick={() => load()} type="button" variant="secondary">
          Actualizar
        </Button>
      </div>

      <Panel className="p-5">
        <form className="grid gap-4 lg:grid-cols-[1fr_1fr_1fr_auto]" onSubmit={applyFilters}>
          <Input label="Modulo" onChange={(event) => setModuleFilter(event.target.value)} placeholder="acceso_usuarios" value={moduleFilter} />
          <Input label="Accion" onChange={(event) => setActionFilter(event.target.value)} placeholder="UPDATE_USER" value={actionFilter} />
          <label className="grid gap-1.5 text-sm font-medium text-slate-700">
            Usuario
            <select
              className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm text-ink outline-none focus:border-accent"
              onChange={(event) => setUserFilter(event.target.value)}
              value={userFilter}
            >
              <option value="">Todos</option>
              {users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.full_name}
                </option>
              ))}
            </select>
          </label>
          <Button className="self-end" icon={<Filter size={16} aria-hidden="true" />} type="submit">
            Filtrar
          </Button>
        </form>
      </Panel>

      {message && <p className="rounded-md bg-slate-50 px-4 py-3 text-sm text-slate-700">{message}</p>}

      <Panel className="overflow-hidden">
        <div className="flex items-center gap-3 border-b border-slate-200 p-5">
          <ClipboardList className="text-accent" size={22} aria-hidden="true" />
          <div>
            <h2 className="text-lg font-semibold">Eventos registrados</h2>
            <p className="text-sm text-slate-500">{logs.length} eventos encontrados</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Modulo</th>
                <th className="px-4 py-3">Accion</th>
                <th className="px-4 py-3">Resultado</th>
                <th className="px-4 py-3">Detalle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => {
                const user = log.user_id ? usersById.get(log.user_id) : undefined;
                return (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-4 py-3 text-slate-600">{formatDate(log.created_at)}</td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-ink">{user?.full_name ?? "Sistema"}</p>
                      <p className="text-xs text-slate-500">{user?.email ?? log.user_id ?? "Sin usuario"}</p>
                    </td>
                    <td className="px-4 py-3">{log.module}</td>
                    <td className="px-4 py-3 font-medium">{log.action}</td>
                    <td className="px-4 py-3">
                      <StatusBadge tone={log.result === "success" ? "success" : "danger"}>{log.result}</StatusBadge>
                    </td>
                    <td className="max-w-md px-4 py-3 text-slate-600">
                      <p>{log.detail ?? "Sin detalle"}</p>
                      <p className="mt-1 truncate text-xs text-slate-400" title={metadataPreview(log.metadata_json)}>
                        {metadataPreview(log.metadata_json)}
                      </p>
                    </td>
                  </tr>
                );
              })}
              {!isLoading && logs.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-center text-slate-500" colSpan={6}>
                    No hay eventos para los filtros aplicados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </section>
  );
}
