# Guía de Permisos por Rol y Uso en Frontend

Este documento detalla el modelo de control de acceso por rol del proyecto (CASE Inteligente - Mejoras 2.º Parcial) y cómo utilizar el hook y los componentes en el frontend.

---

## 1. Roles del Proyecto y Permisos por Defecto

Los roles disponibles son:
- **`ORGANIZADOR`**: Propietario o administrador del proyecto. Cuenta con todos los permisos (11 permisos).
- **`EDITOR`**: Diseñador/desarrollador que modela UML, chatea con la IA, genera código y edita temas. No administra integrantes, no actualiza metadatos del proyecto ni crea/restaura versiones.
- **`LECTOR`**: Solo lectura. Puede ver el proyecto (`project.read`), explorar diagramas y revisar el historial de cambios. No puede modificar UML, no puede chatear ni confirmar acciones con la IA, no puede ejecutar generaciones ni editar temas.

### Matriz de Códigos de Permiso

| Código | Descripción | ORGANIZADOR | EDITOR | LECTOR |
| :--- | :--- | :---: | :---: | :---: |
| `project.read` | Ver proyecto y miembros | ✅ | ✅ | ✅ |
| `project.update` | Actualizar nombre y descripción del proyecto | ✅ | ❌ | ❌ |
| `members.manage` | Invitar, modificar rol y permisos de miembros | ✅ | ❌ | ❌ |
| `uml.edit` | Crear, editar y borrar clases, atributos, métodos, relaciones | ✅ | ✅ | ❌ |
| `versions.create` | Crear versiones e instantáneas del proyecto | ✅ | ❌ | ❌ |
| `versions.restore` | Restaurar proyecto a una versión anterior | ✅ | ❌ | ❌ |
| `ai.chat` | Enviar mensajes al asistente de IA del proyecto | ✅ | ✅ | ❌ |
| `ai.confirm_actions` | Confirmar o rechazar acciones propuestas por la IA | ✅ | ✅ | ❌ |
| `ai.settings` | Modificar configuración del asistente (proveedor, proactividad) | ✅ | ❌ | ❌ |
| `generation.run` | Disparar generación coordinada (Spring Boot / Flutter) | ✅ | ✅ | ❌ |
| `theme.edit` | Editar estilos Flutter y guardar presets | ✅ | ✅ | ❌ |

---

## 2. Consumo en Frontend

### Hook `useProjectPermissions`

Ubicación: `frontend/src/core/permissions/useProjectPermissions.ts`

```tsx
import { useProjectPermissions } from "@/core/permissions/useProjectPermissions";

export function MiComponente({ projectId }: { projectId: string }) {
  const { role, can, loading, refresh } = useProjectPermissions(projectId);

  if (loading) {
    return <Skeleton className="h-8 w-24" />;
  }

  return (
    <div>
      <p>Mi rol actual: {role}</p>
      {can("uml.edit") && (
        <button onClick={handleAddClass}>Crear clase</button>
      )}
      {can("ai.confirm_actions") && (
        <button onClick={handleConfirmAction}>Aceptar propuesta</button>
      )}
    </div>
  );
}
```

- **Caché en Zustand:** Los permisos se almacenan en memoria con un TTL de 60 segundos por `projectId`.
- **Deduplicación:** Múltiples componentes que solicitan permisos para el mismo `projectId` comparten una única petición HTTP a `GET /projects/{id}/members/me`.
- **Refresco forzado:** Al recibir un error `403 PERMISSION_DENIED` desde cualquier endpoint, llamar a `refresh()` para invalidar la caché y reconsultar la membresía actual.

### Componente `PermissionGate`

Ubicación: `frontend/src/core/permissions/PermissionGate.tsx`

Permite ocultar o mostrar condicionalmente elementos del árbol de React con un `fallback` opcional.

```tsx
import { PermissionGate } from "@/core/permissions/PermissionGate";

<PermissionGate
  projectId={projectId}
  code="members.manage"
  fallback={<span className="text-xs text-slate-400">Solo organizadores</span>}
>
  <button onClick={handleOpenInviteModal}>Invitar integrante</button>
</PermissionGate>
```
