import type { ReactNode } from "react";
import type { CodigoPermiso } from "../contracts/mejoras2p";
import { usePermisosProyecto } from "./usePermisosProyecto";

export interface PropiedadesControlPermisos {
  projectId: string;
  code: CodigoPermiso;
  children: ReactNode;
  fallback?: ReactNode;
}

export function ControlPermisos({
  projectId,
  code,
  children,
  fallback = null,
}: PropiedadesControlPermisos) {
  const { can, loading } = usePermisosProyecto(projectId);

  if (loading) {
    return <>{fallback}</>;
  }

  return can(code) ? <>{children}</> : <>{fallback}</>;
}
