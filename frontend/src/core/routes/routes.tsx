import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { useAuthStore } from "../auth/authStore";
import { LoginPage } from "../../modules/gestion_acceso_usuarios/pages/LoginPage";
import { RegisterPage } from "../../modules/gestion_acceso_usuarios/pages/RegisterPage";
import { ProfilePage } from "../../modules/gestion_acceso_usuarios/pages/ProfilePage";
import { ReportsPage } from "../../modules/gestion_acceso_usuarios/pages/ReportsPage";
import { ProjectManagementPage } from "../../modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage";
import { ProjectsPage } from "../../modules/gestion_proyectos_colaboracion/pages/ProjectsPage";
import { ProjectWorkspacePage } from "../../modules/gestion_proyectos_colaboracion/pages/ProjectWorkspacePage";
import { UmlEditorPage } from "../../modules/modelado_uml_inteligente/pages/UmlEditorPage";
import { GenerationPage } from "../../modules/transformacion_generacion_software/pages/GenerationPage";
import { AppLayout } from "../../shared/layouts/AppLayout";

function ProtectedRoute() {
  const token = useAuthStore((state) => state.token);
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/registro" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/proyectos" replace />} />
          <Route path="/proyectos" element={<ProjectsPage />} />
          <Route path="/proyectos/:projectId" element={<ProjectManagementPage />} />
          <Route path="/proyectos/:projectId/colaborativo" element={<ProjectWorkspacePage />} />
          <Route path="/proyectos/:projectId/uml/:diagramId" element={<UmlEditorPage />} />
          <Route path="/generacion" element={<GenerationPage />} />
          <Route path="/perfil" element={<ProfilePage />} />
          <Route path="/reportes" element={<ReportsPage />} />
          <Route path="/manual" element={<Navigate to="/proyectos" replace />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
