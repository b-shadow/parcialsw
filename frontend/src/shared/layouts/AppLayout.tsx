import { BarChart3, BookOpen, Box, Code2, FolderKanban, LogOut, User } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuthStore } from "../../core/auth/authStore";
import { cn } from "../utils/cn";

const navItems = [
  { to: "/proyectos", label: "Proyectos", icon: FolderKanban },
  { to: "/generacion", label: "Generacion", icon: Code2 },
  { to: "/reportes", label: "Reportes", icon: BarChart3 },
  { to: "/manual", label: "Manual", icon: BookOpen },
  { to: "/perfil", label: "Perfil", icon: User }
];

export function AppLayout() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return (
    <div className="min-h-screen bg-panel text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:block">
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-white">
            <Box size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold">CASE Inteligente</p>
            <p className="text-xs text-slate-500">Frontend modular</p>
          </div>
        </div>
        <nav className="grid gap-1 p-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex h-10 items-center gap-3 rounded-md px-3 text-sm font-medium text-slate-600",
                    isActive && "bg-teal-50 text-accent"
                  )
                }
              >
                <Icon size={18} aria-hidden="true" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur md:px-6">
          <div>
            <p className="text-sm font-semibold">Plataforma CASE</p>
            <p className="text-xs text-slate-500">{user?.email ?? "Sesion activa"}</p>
          </div>
          <button
            className="inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm font-medium text-slate-600 hover:bg-slate-100"
            onClick={() => {
              logout();
              navigate("/login");
            }}
            title="Cerrar sesion"
          >
            <LogOut size={18} aria-hidden="true" />
            <span className="hidden sm:inline">Salir</span>
          </button>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 md:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
