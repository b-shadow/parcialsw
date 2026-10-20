"""Catálogo y cálculo de permisos por rol de proyecto."""

from collections.abc import Iterable

PERMISSION_CODES: frozenset[str] = frozenset({
    "project.read",
    "project.update",
    "members.manage",
    "uml.edit",
    "versions.create",
    "versions.restore",
    "ai.chat",
    "ai.confirm_actions",
    "ai.settings",
    "generation.run",
    "theme.edit",
})

PROJECT_ROLES: tuple[str, ...] = ("ORGANIZADOR", "EDITOR", "LECTOR")

ROLE_DEFAULTS: dict[str, frozenset[str]] = {
    "ORGANIZADOR": PERMISSION_CODES,
    "EDITOR": frozenset({
        "project.read",
        "uml.edit",
        "versions.create",
        "ai.chat",
        "ai.confirm_actions",
        "generation.run",
        "theme.edit",
    }),
    "LECTOR": frozenset({
        "project.read",
        "ai.chat",
    }),
}


def effective_permissions(project_role: str, granted: Iterable[str]) -> frozenset[str]:
    """Calcula los permisos efectivos de un miembro: base del rol + concedidos válidos."""
    base = ROLE_DEFAULTS.get(project_role, frozenset())
    valid_granted = set(granted) & PERMISSION_CODES
    return base | valid_granted
