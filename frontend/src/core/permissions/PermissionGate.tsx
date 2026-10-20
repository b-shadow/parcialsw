import type { ReactNode } from "react";
import type { PermissionCode } from "../contracts/mejoras2p";
import { useProjectPermissions } from "./useProjectPermissions";

export interface PermissionGateProps {
  projectId: string;
  code: PermissionCode;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({
  projectId,
  code,
  children,
  fallback = null,
}: PermissionGateProps) {
  const { can, loading } = useProjectPermissions(projectId);

  if (loading) {
    return <>{fallback}</>;
  }

  return can(code) ? <>{children}</> : <>{fallback}</>;
}
