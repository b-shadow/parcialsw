"""Pruebas de contratos compartidos y validaciones (V0.3 y V0.4)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.changelog.contratos import construir_resumen
from app.modules.asistente_proyecto.schemas.eventos_websocket import (
    ActorWebSocketV2,
    EventoWebSocketV2,
)
from app.modules.modelado_uml.services.servicio_uml import ServicioUML
from app.modules.proyectos_colaboracion.permisos import (
    PERMISSION_CODES,
    ROLE_DEFAULTS,
    permisos_efectivos,
)


def test_role_defaults_lector():
    assert ROLE_DEFAULTS["LECTOR"] == {"project.read", "ai.chat"}


def test_effective_permissions_are_fixed_by_role():
    perms = permisos_efectivos("EDITOR")
    assert "members.manage" not in perms
    assert "uml.edit" in perms  # Por defecto en EDITOR
    assert permisos_efectivos("UNKNOWN") == frozenset()


def test_all_role_defaults_are_in_permission_codes():
    for role, default_perms in ROLE_DEFAULTS.items():
        assert default_perms.issubset(PERMISSION_CODES), f"Permisos desconocidos en rol {role}"


def test_websocket_event_v2_validation():
    now = datetime.now(UTC)
    ev_id = uuid4()
    proj_id = uuid4()
    corr_id = uuid4()

    event = EventoWebSocketV2(
        type="CHANGE_LOGGED",
        event_id=ev_id,
        project_id=proj_id,
        sequence_number=1,
        correlation_id=corr_id,
        occurred_at=now,
        actor=ActorWebSocketV2(display_name="Test User"),
        payload={"sample": "data"},
    )
    assert event.type == "CHANGE_LOGGED"

    with pytest.raises(ValidationError):
        EventoWebSocketV2(
            type="EVENTO_INEXISTENTE",
            event_id=ev_id,
            project_id=proj_id,
            sequence_number=1,
            correlation_id=corr_id,
            occurred_at=now,
            actor=ActorWebSocketV2(display_name="Test User"),
            payload={},
        )


def test_build_summary_formatting():
    assert construir_resumen("CREATE_CLASS", {"name": "Producto"}) == "Creó la clase Producto"
    assert construir_resumen("DELETE_CLASS", {"class_name": "Factura"}) == "Eliminó la clase Factura"
    assert construir_resumen("CREATE_PROJECT_VERSION", {}) == "Guardó una versión"


def test_class_name_uniqueness_check():
    mock_db = MagicMock()
    service = ServicioUML(mock_db)

    diagram_id = uuid4()
    existing_cls = MagicMock()
    existing_cls.id = uuid4()
    existing_cls.name = "Producto"

    service.uml = MagicMock()
    service.uml.listar_clases.return_value = [existing_cls]

    # Nombre repetido exacto
    with pytest.raises(HTTPException) as exc_info:
        service._asegurar_nombre_clase_unico(diagram_id, "Producto")
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "CLASS_NAME_DUPLICATED"

    # Nombre repetido con mayúsculas/minúsculas y espacios
    with pytest.raises(HTTPException) as exc_info:
        service._asegurar_nombre_clase_unico(diagram_id, "  pRoDuCtO  ")
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "CLASS_NAME_DUPLICATED"

    # Mismo id al actualizar no debe lanzar error
    service._asegurar_nombre_clase_unico(diagram_id, "producto", exclude_id=existing_cls.id)

    # Nombre diferente no debe lanzar error
    service._asegurar_nombre_clase_unico(diagram_id, "Cliente")
