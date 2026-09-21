import { FormEvent, useEffect, useState } from "react";
import { KeyRound, Mail, Save, ShieldCheck, UserRound } from "lucide-react";

import { useAuthStore } from "../../../core/auth/authStore";
import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { authService } from "../services/authService";
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

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    authService.me().then(setUser).catch(() => undefined);
  }, [setUser]);

  async function handlePasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    if (newPassword !== confirmPassword) {
      setMessage("La nueva contrasena y la confirmacion no coinciden.");
      return;
    }
    setIsSaving(true);
    try {
      await userService.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage("Contrasena actualizada correctamente.");
    } catch (error) {
      const detail = error instanceof Error ? error.message : "No se pudo cambiar la contrasena.";
      setMessage(detail);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Perfil</h1>
        <p className="text-sm text-slate-500">Cuenta activa, seguridad y preferencias de acceso.</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_1.15fr]">
        <Panel className="grid gap-5 p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent text-white">
                <UserRound size={22} aria-hidden="true" />
              </div>
              <div>
                <h2 className="text-lg font-semibold">{user?.full_name ?? "Usuario autenticado"}</h2>
                <p className="text-sm text-slate-500">Perfil del sistema CASE</p>
              </div>
            </div>
            <StatusBadge tone={user?.is_active === false ? "danger" : "success"}>
              {user?.is_active === false ? "inactive" : "active"}
            </StatusBadge>
          </div>

          <div className="grid gap-3">
            <div className="rounded-md border border-slate-200 p-4">
              <p className="mb-1 inline-flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
                <Mail size={14} aria-hidden="true" />
                Correo
              </p>
              <p className="text-sm font-medium text-ink">{user?.email ?? "Sincronizando perfil"}</p>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Ultimo acceso</p>
                <p className="mt-1 text-sm font-medium text-ink">{formatDate(user?.last_access_at)}</p>
              </div>
              <div className="rounded-md border border-slate-200 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">Cuenta creada</p>
                <p className="mt-1 text-sm font-medium text-ink">{formatDate(user?.created_at)}</p>
              </div>
            </div>
          </div>
        </Panel>

        <Panel className="p-5">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-accent">
              <ShieldCheck size={20} aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Seguridad</h2>
              <p className="text-sm text-slate-500">Actualiza tu contrasena de acceso.</p>
            </div>
          </div>

          <form className="grid gap-4" onSubmit={handlePasswordChange}>
            <Input
              label="Contrasena actual"
              onChange={(event) => setCurrentPassword(event.target.value)}
              required
              type="password"
              value={currentPassword}
            />
            <div className="grid gap-4 md:grid-cols-2">
              <Input
                label="Nueva contrasena"
                minLength={8}
                onChange={(event) => setNewPassword(event.target.value)}
                required
                type="password"
                value={newPassword}
              />
              <Input
                label="Confirmar contrasena"
                minLength={8}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
                type="password"
                value={confirmPassword}
              />
            </div>
            {message && (
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
                {message}
              </p>
            )}
            <Button disabled={isSaving} icon={<KeyRound size={16} aria-hidden="true" />} type="submit">
              {isSaving ? "Actualizando..." : "Cambiar contrasena"}
            </Button>
          </form>
        </Panel>
      </div>

      <Panel className="flex flex-wrap items-center justify-between gap-3 p-5">
        <div>
          <h2 className="text-base font-semibold">Sesion y acceso</h2>
          <p className="text-sm text-slate-500">Mantén tus credenciales actualizadas para proteger proyectos y diagramas.</p>
        </div>
        <Button icon={<Save size={16} aria-hidden="true" />} variant="secondary" type="button">
          Perfil sincronizado
        </Button>
      </Panel>
    </section>
  );
}
