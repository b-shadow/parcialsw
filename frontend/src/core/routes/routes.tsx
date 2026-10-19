import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { useAuthStore } from "../auth/authStore";
import { AppLayout } from "../../shared/layouts/AppLayout";

const LoginPage = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/LoginPage").then((module) => ({ default: module.LoginPage })));
const RegisterPage = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/RegisterPage").then((module) => ({ default: module.RegisterPage })));
const ProfilePage = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/ProfilePage").then((module) => ({ default: module.ProfilePage })));
const ReportsPage = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const AdminUsersPage = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/AdminUsersPage").then((module) => ({ default: module.AdminUsersPage })));
const AuditLogPage = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/AuditLogPage").then((module) => ({ default: module.AuditLogPage })));
const ProjectManagementPage = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage").then((module) => ({ default: module.ProjectManagementPage })));
const ProjectsPage = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/ProjectsPage").then((module) => ({ default: module.ProjectsPage })));
const CreateProjectPage = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/CreateProjectPage").then((module) => ({ default: module.CreateProjectPage })));
const ProjectWorkspacePage = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/ProjectWorkspacePage").then((module) => ({ default: module.ProjectWorkspacePage })));
const UmlEditorPage = lazy(() => import("../../modules/modelado_uml_inteligente/pages/UmlEditorPage").then((module) => ({ default: module.UmlEditorPage })));
const GenerationPage = lazy(() => import("../../modules/transformacion_generacion_software/pages/GenerationPage").then((module) => ({ default: module.GenerationPage })));

function ProtectedRoute() {
  const token = useAuthStore((state) => state.token);
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <Suspense fallback={<div className="grid min-h-screen place-items-center text-sm text-slate-600">Cargando...</div>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/registro" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/proyectos/nuevo" replace />} />
            <Route path="/proyectos" element={<ProjectsPage />} />
            <Route path="/proyectos/nuevo" element={<CreateProjectPage />} />
            <Route path="/proyectos/:projectId" element={<ProjectManagementPage />} />
            <Route path="/proyectos/:projectId/colaborativo" element={<ProjectWorkspacePage />} />
            <Route path="/proyectos/:projectId/uml/:diagramId" element={<UmlEditorPage />} />
            <Route path="/proyectos/:projectId/generacion" element={<GenerationPage />} />
            <Route path="/generacion" element={<Navigate to="/proyectos" replace />} />
            <Route path="/perfil" element={<ProfilePage />} />
            <Route path="/reportes" element={<ReportsPage />} />
            <Route path="/usuarios" element={<AdminUsersPage />} />
            <Route path="/bitacora" element={<AuditLogPage />} />
            <Route path="/manual" element={<Navigate to="/proyectos" replace />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
