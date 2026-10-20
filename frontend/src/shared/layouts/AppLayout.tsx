import { useEffect, useState } from "react";
import { BarChart3, Box, ClipboardList, Code2, FolderKanban, LogOut, Menu, Plus, ShieldCheck, User, Users, X } from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuthStore } from "../../core/auth/authStore";
import { useThemeStore } from "../../core/theme/themeStore";
import { authService } from "../../modules/gestion_acceso_usuarios/services/authService";
import { ProjectAiAssistant } from "../../modules/gestion_proyectos_colaboracion/components/ProjectAiAssistant";
import { ProjectPresenceIndicator } from "../../modules/gestion_proyectos_colaboracion/components/ProjectPresenceIndicator";
import { AssistantWidget } from "../components/AssistantWidget";
import { PushNotificationButton } from "../components/PushNotificationButton";
import { NotificationCenter } from "../components/NotificationCenter";
import { ThemeToggle } from "../components/ThemeToggle";
import { Toaster } from "../components/Toaster";
import { ConfirmDialogHost } from "../components/ConfirmDialog";
import { cn } from "../utils/cn";

const navItems = [
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
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 1024);
  const isAdmin = user?.role_names?.includes("ADMINISTRADOR") ?? false;

  useEffect(() => {
    if (!user) {
      authService.me().then(setUser).catch(() => undefined);
    }
  }, [setUser, user]);

  useEffect(() => {
    if (!sidebarOpen) return;
    function closeWithEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setSidebarOpen(false);
    }
    window.addEventListener("keydown", closeWithEscape);
    return () => window.removeEventListener("keydown", closeWithEscape);
  }, [sidebarOpen]);

  const isCreateProjectRoute = location.pathname === "/proyectos/nuevo";
  const isProjectsRoute = location.pathname.startsWith("/proyectos") && !isCreateProjectRoute;
  const projectMatch = location.pathname.match(/^\/proyectos\/([^/]+)/);
  const matchedProjectId = projectMatch?.[1];
  const currentProjectId = matchedProjectId && matchedProjectId !== "nuevo" ? matchedProjectId : undefined;
  const diagramMatch = location.pathname.match(/\/uml\/([^/]+)/);
  const currentDiagramId = diagramMatch?.[1] ?? null;
  const isProjectManagementRoute =
    /^\/proyectos\/[^/]+\/?$/.test(location.pathname) && location.pathname !== "/proyectos/nuevo";
  const isProjectCollaborativeRoute =
    /^\/proyectos\/[^/]+\/colaborativo\/?$/.test(location.pathname) ||
    /^\/proyectos\/[^/]+\/uml\/[^/]+\/?$/.test(location.pathname);
  const isProjectGenerationRoute =
    /^\/proyectos\/[^/]+\/generacion\/?$/.test(location.pathname);
  const managementPath = currentProjectId ? `/proyectos/${currentProjectId}` : "/proyectos";
  const collaborativePath = currentProjectId ? `/proyectos/${currentProjectId}/colaborativo` : "/proyectos";
  const generationPath = currentProjectId ? `/proyectos/${currentProjectId}/generacion` : "/proyectos";

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
      {sidebarOpen && (
        <button
          aria-label="Cerrar menú lateral"
          className="fixed inset-x-0 bottom-0 top-20 z-30 bg-slate-950/35 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          type="button"
        />
      )}
      <aside
        className={cn(
          "fixed bottom-0 left-0 top-20 z-40 flex w-72 flex-col border-r transition-transform duration-200 lg:inset-y-0 lg:top-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          sidebarTone
        )}
      >
        <div className={cn("flex h-20 items-center gap-4 border-b px-6", isDark ? "border-slate-800" : "border-slate-200")}>
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-white shadow-lg shadow-teal-900/15">
            <Box size={20} aria-hidden="true" />
          </div>
          <div>
            <p className="text-xl font-black tracking-tight">CASE Inteligente</p>
            <p className={cn("text-xs font-medium", isDark ? "text-slate-400" : "text-slate-500")}>Frontend modular</p>
          </div>
          <button
            aria-label="Cerrar menú lateral"
            className={cn("ml-auto grid size-9 place-items-center rounded-md lg:hidden", inactiveNavTone)}
            onClick={() => setSidebarOpen(false)}
            title="Cerrar menú lateral"
            type="button"
          >
            <X size={20} aria-hidden="true" />
          </button>
        </div>

        <nav className="grid gap-2 p-6">
          <NavLink
            to="/proyectos/nuevo"
            className={cn(
              "flex h-12 items-center gap-4 rounded-lg px-4 text-base font-semibold transition",
              isCreateProjectRoute ? activeNavTone : inactiveNavTone
            )}
          >
            <Plus size={22} aria-hidden="true" />
            Crear proyecto
          </NavLink>

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

            {currentProjectId ? <NavLink
              to={managementPath}
              className={cn(
                "ml-4 flex h-11 items-center gap-3 rounded-lg px-4 text-base font-semibold transition",
                isProjectManagementRoute ? activeNavTone : inactiveNavTone
              )}
            >
              <User size={21} aria-hidden="true" />
              Gestionar
            </NavLink> : null}

            {currentProjectId ? <NavLink
              to={collaborativePath}
              className={cn(
                "ml-4 flex h-11 items-center gap-3 rounded-lg px-4 text-base font-semibold transition",
                isProjectCollaborativeRoute ? activeNavTone : inactiveNavTone
              )}
            >
              <Users size={21} aria-hidden="true" />
              Colaborativo
            </NavLink> : null}

            {currentProjectId ? <NavLink
              to={generationPath}
              className={cn(
                "ml-4 flex h-11 items-center gap-3 rounded-lg px-4 text-base font-semibold transition",
                isProjectGenerationRoute ? activeNavTone : inactiveNavTone
              )}
            >
              <Code2 size={21} aria-hidden="true" />
              Generacion
            </NavLink> : null}
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

      <div className={cn("transition-[padding] duration-200", sidebarOpen ? "lg:pl-72" : "lg:pl-0")}>
        <header className={cn("sticky top-0 z-20 flex h-20 items-center justify-between border-b px-4 backdrop-blur md:px-8", topbarTone)}>
          <div className="flex min-w-0 items-center gap-3">
            <button
              aria-expanded={sidebarOpen}
              aria-label={sidebarOpen ? "Ocultar menú lateral" : "Mostrar menú lateral"}
              className={cn("grid size-10 shrink-0 place-items-center rounded-md transition", inactiveNavTone)}
              onClick={() => setSidebarOpen((open) => !open)}
              title={sidebarOpen ? "Ocultar menú lateral" : "Mostrar menú lateral"}
              type="button"
            >
              <Menu size={22} aria-hidden="true" />
            </button>
            <div className="min-w-0">
              <p className="text-base font-black"><span className="sm:hidden">CASE</span><span className="hidden sm:inline">Plataforma CASE</span></p>
              <div className="flex min-w-0 items-center gap-1.5">
                <p className={cn("hidden max-w-44 truncate text-xs min-[460px]:block", isDark ? "text-slate-400" : "text-slate-500")}>{user?.email ?? "Sesion activa"}</p>
                {currentProjectId && <ProjectPresenceIndicator />}
              </div>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-5">
            <NotificationCenter />
            <span className="hidden sm:inline-flex"><PushNotificationButton /></span>
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
      {currentProjectId && !currentDiagramId && (
        <ProjectAiAssistant projectId={currentProjectId} diagramId={currentDiagramId} />
      )}
      {!currentDiagramId && <AssistantWidget />}
      <Toaster />
      <ConfirmDialogHost />
    </div>
  );
}
