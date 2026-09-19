import { useEffect } from "react";

import { useAuthStore } from "../../../core/auth/authStore";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { authService } from "../services/authService";

export function ProfilePage() {
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    authService.me().then(setUser).catch(() => undefined);
  }, [setUser]);

  return (
    <section className="grid gap-4">
      <h1 className="text-2xl font-semibold">Perfil</h1>
      <Panel className="grid gap-3 p-5">
        <div>
          <p className="text-xs font-medium uppercase text-slate-500">Nombre</p>
          <p className="text-base font-semibold">{user?.full_name ?? "Usuario autenticado"}</p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase text-slate-500">Correo</p>
          <p className="text-sm text-slate-700">{user?.email ?? "Sincronizando perfil"}</p>
        </div>
        <div>
          <p className="text-xs font-medium uppercase text-slate-500">Estado</p>
          <StatusBadge tone="success">{user?.status ?? "active"}</StatusBadge>
        </div>
      </Panel>
    </section>
  );
}
