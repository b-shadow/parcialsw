import { useEffect } from "react";
import { BarChart3, Box, ClipboardList, Code2, FolderKanban, LogOut, ShieldCheck, User, Users } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "../../core/auth/authStore";
import { useThemeStore } from "../../core/theme/themeStore";
import { authService } from "../../modules/gestion_acceso_usuarios/services/authService";
import { AssistantWidget } from "../components/AssistantWidget";
import { ThemeToggle } from "../components/ThemeToggle";
import { cn } from "../utils/cn";

const navItems = [
  { to: "/generacion", label: "Generacion", icon: Code2 },
  { to: "/reportes", label: "Reportes", icon: BarChart3 },
  { to: "/perfil", label: "Perfil", icon: User }
];

const adminNavItems = [
  { to: "/usuarios", label: "Usuarios", icon: ShieldCheck },
  { to: "/bitacora", label: "Bitacora", icon: ClipboardList }
];

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const isDark = useThemeStore((state) => state.mode === "dark");
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const logout = useAuthStore((state) => state.logout);
  const isAdmin = user?.role_names?.includes("ADMINISTRADOR") ?? false;

  useEffect(() => {
    if (!user) {
      authService.me().then(setUser).catch(() => undefined);
    }
  }, [setUser, user]);

  const isProjectsRoute = location.pathname.startsWith("/proyectos");
  const projectMatch = location.pathname.match(/^\/proyectos\/([^/]+)/);
  const currentProjectId = projectMatch?.[1];
  const isProjectManagementRoute =
    /^\/proyectos\/[^/]+\/?$/.test(location.pathname);
  const isProjectCollaborativeRoute =
    /^\/proyectos\/[^/]+\/colaborativo\/?$/.test(location.pathname) ||
    /^\/proyectos\/[^/]+\/uml\/[^/]+\/?$/.test(location.pathname);
  const managementPath = currentProjectId ? `/proyectos/${currentProjectId}` : "/proyectos";
  const collaborativePath = currentProjectId ? `/proyectos/${currentProjectId}/colaborativo` : "/proyectos";

  const shellTone = isDark
    ? "bg-[#07111f] text-slate-100"
    : "bg-[linear-gradient(135deg,#f8fbff_0%,#eff9fb_52%,#f7f8fb_100%)] text-[#070b5f]";
  const sidebarTone = isDark ? "border-slate-800 bg-[#0b1424]" : "border-slate-200 bg-white";
  const topbarTone = isDark ? "border-slate-800 bg-[#0b1424]/95" : "border-slate-200 bg-white/96";
  const inactiveNavTone = isDark
    ? "text-slate-300 hover:bg-slate-800"
    : "text-blue-900 hover:bg-teal-50";
  const activeNavTone = isDark
    ? "bg-teal-400/10 text-teal-300"
    : "bg-teal-50 text-accent";

  return (
    <div className={cn("min-h-screen", shellTone)}>
      <aside className={cn("fixed inset-y-0 left-0 hidden w-72 border-r lg:flex lg:flex-col", sidebarTone)}>
        <div className={cn("flex h-20 items-center gap-4 border-b px-6", isDark ? "border-slate-800" : "border-slate-200")}>
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-white shadow-lg shadow-teal-900/15">
            <Box size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="text-xl font-black tracking-tight">CASE Inteligente</p>
            <p className={cn("text-xs font-medium", isDark ? "text-slate-400" : "text-slate-500")}>Frontend modular</p>
          </div>
        </div>

        <nav className="grid gap-2 p-6">
          <div className="grid gap-2">
            <NavLink
              to="/proyectos"
              className={cn(
                "flex h-12 items-center justify-between rounded-lg px-4 text-base font-bold transition",
                isProjectsRoute ? activeNavTone : inactiveNavTone
              )}
            >
              <span className="inline-flex items-center gap-3">
                <FolderKanban size={22} aria-hidden="true" />
                Proyectos
              </span>
              <span className="text-xl leading-none">^</span>
            </NavLink>

            <NavLink
              to={managementPath}
              className={cn(
                "ml-4 flex h-11 items-center gap-3 rounded-lg px-4 text-base font-semibold transition",
                isProjectManagementRoute ? activeNavTone : inactiveNavTone
              )}
            >
              <User size={21} aria-hidden="true" />
              Gestionar
            </NavLink>

            <NavLink
              to={collaborativePath}
              className={cn(
                "ml-4 flex h-11 items-center gap-3 rounded-lg px-4 text-base font-semibold transition",
                isProjectCollaborativeRoute ? activeNavTone : inactiveNavTone
              )}
            >
              <Users size={21} aria-hidden="true" />
              Colaborativo
            </NavLink>
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex h-12 items-center gap-4 rounded-lg px-4 text-base font-semibold transition",
                    isActive ? activeNavTone : inactiveNavTone
                  )
                }
              >
                <Icon size={22} aria-hidden="true" />
                {item.label}
              </NavLink>
            );
          })}

          {isAdmin && (
            <div className="mt-2 grid gap-2 border-t border-slate-200 pt-4 dark:border-slate-800">
              {adminNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      cn(
                        "flex h-12 items-center gap-4 rounded-lg px-4 text-base font-semibold transition",
                        isActive ? activeNavTone : inactiveNavTone
                      )
                    }
                  >
                    <Icon size={22} aria-hidden="true" />
                    {item.label}
                  </NavLink>
                );
              })}
            </div>
          )}
        </nav>

        <div className="mt-auto p-6">
          <div className={cn("rounded-lg p-5", isDark ? "bg-slate-900 text-slate-300" : "bg-teal-50 text-blue-900")}>
            <div className="mb-5 h-1 w-12 rounded-full bg-accent" />
            <p className="text-base leading-6">
              Modela.
              <br />
              Colabora.
              <br />
              Genera.
              <br />
              Construye el futuro.
            </p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-72">
        <header className={cn("sticky top-0 z-20 flex h-20 items-center justify-between border-b px-4 backdrop-blur md:px-8", topbarTone)}>
          <div>
            <p className="text-base font-black">Plataforma CASE</p>
            <p className={cn("text-xs", isDark ? "text-slate-400" : "text-slate-500")}>{user?.email ?? "Sesion activa"}</p>
          </div>
          <div className="flex items-center gap-5">
            <ThemeToggle />
            <div className={cn("hidden h-7 w-px sm:block", isDark ? "bg-slate-700" : "bg-slate-200")} />
            <button
              className="inline-flex h-11 items-center gap-3 rounded-lg border border-red-500 px-5 text-base font-bold text-red-600 transition hover:bg-red-50 dark:hover:bg-red-500/10"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              title="Cerrar sesion"
            >
              <LogOut size={18} aria-hidden="true" />
              <span className="hidden sm:inline">Cerrar sesion</span>
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-[1480px] px-4 py-8 md:px-8">
          <Outlet />
        </main>
      </div>
      <AssistantWidget />
    </div>
  );
}
