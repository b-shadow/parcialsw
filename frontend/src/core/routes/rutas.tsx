import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { useAlmacenAutenticacion } from "../auth/almacenAutenticacion";
import { DisposicionAplicacion } from "../../shared/layouts/DisposicionAplicacion";

const PaginaIngreso = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/PaginaIngreso").then((module) => ({ default: module.PaginaIngreso })));
const PaginaRegistro = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/PaginaRegistro").then((module) => ({ default: module.PaginaRegistro })));
const PaginaPerfil = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/PaginaPerfil").then((module) => ({ default: module.PaginaPerfil })));
const PaginaReportes = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/PaginaReportes").then((module) => ({ default: module.PaginaReportes })));
const PaginaUsuariosAdmin = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/PaginaUsuariosAdmin").then((module) => ({ default: module.PaginaUsuariosAdmin })));
const PaginaRegistroAuditoria = lazy(() => import("../../modules/gestion_acceso_usuarios/pages/PaginaRegistroAuditoria").then((module) => ({ default: module.PaginaRegistroAuditoria })));
const PaginaGestionProyecto = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/PaginaGestionProyecto").then((module) => ({ default: module.PaginaGestionProyecto })));
const PaginaProyectos = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/PaginaProyectos").then((module) => ({ default: module.PaginaProyectos })));
const PaginaCrearProyecto = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/PaginaCrearProyecto").then((module) => ({ default: module.PaginaCrearProyecto })));
const PaginaEspacioProyecto = lazy(() => import("../../modules/gestion_proyectos_colaboracion/pages/PaginaEspacioProyecto").then((module) => ({ default: module.PaginaEspacioProyecto })));
const PaginaEditorUML = lazy(() => import("../../modules/modelado_uml_inteligente/pages/PaginaEditorUML").then((module) => ({ default: module.PaginaEditorUML })));
const PaginaGeneracion = lazy(() => import("../../modules/transformacion_generacion_software/pages/PaginaGeneracion").then((module) => ({ default: module.PaginaGeneracion })));

function ProtectedRoute() {
  const token = useAlmacenAutenticacion((state) => state.token);
  return token ? <Outlet /> : <Navigate to="/login" replace />;
}

export function RutasAplicacion() {
  return (
    <Suspense fallback={<div className="grid min-h-screen place-items-center text-sm text-slate-600">Cargando...</div>}>
      <Routes>
        <Route path="/login" element={<PaginaIngreso />} />
        <Route path="/registro" element={<PaginaRegistro />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DisposicionAplicacion />}>
            <Route index element={<Navigate to="/proyectos/nuevo" replace />} />
            <Route path="/proyectos" element={<PaginaProyectos />} />
            <Route path="/proyectos/nuevo" element={<PaginaCrearProyecto />} />
            <Route path="/proyectos/:projectId" element={<PaginaGestionProyecto />} />
            <Route path="/proyectos/:projectId/colaborativo" element={<PaginaEspacioProyecto />} />
            <Route path="/proyectos/:projectId/uml/:diagramId" element={<PaginaEditorUML />} />
            <Route path="/proyectos/:projectId/generacion" element={<PaginaGeneracion />} />
            <Route path="/generacion" element={<Navigate to="/proyectos" replace />} />
            <Route path="/perfil" element={<PaginaPerfil />} />
            <Route path="/reportes" element={<PaginaReportes />} />
            <Route path="/usuarios" element={<PaginaUsuariosAdmin />} />
            <Route path="/bitacora" element={<PaginaRegistroAuditoria />} />
            <Route path="/manual" element={<Navigate to="/proyectos" replace />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
