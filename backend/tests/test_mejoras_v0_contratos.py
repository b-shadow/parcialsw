"""Pruebas de contratos compartidos y validaciones (V0.3 y V0.4)."""

from datetime import datetime, timezone
from uuid import uuid4
import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from app.core.changelog.contracts import build_summary
from app.modules.asistente_proyecto.schemas.websocket import WebSocketActorV2, WebSocketEventV2
from app.modules.proyectos_colaboracion.permissions import (
    PERMISSION_CODES,
    ROLE_DEFAULTS,
    effective_permissions,
)
from app.modules.modelado_uml.services.uml_service import UmlService
from app.modules.modelado_uml.schemas.uml import UmlClassCreateRequest
from unittest.mock import MagicMock


def test_role_defaults_lector():
    assert ROLE_DEFAULTS["LECTOR"] == {"project.read", "ai.chat"}


def test_effective_permissions_filter_invalid_codes():
    perms = effective_permissions("EDITOR", ["members.manage", "codigo_inventado"])
    assert "members.manage" in perms
    assert "codigo_inventado" not in perms
    assert "uml.edit" in perms  # Por defecto en EDITOR


def test_all_role_defaults_are_in_permission_codes():
    for role, default_perms in ROLE_DEFAULTS.items():
        assert default_perms.issubset(PERMISSION_CODES), f"Permisos desconocidos en rol {role}"


def test_websocket_event_v2_validation():
    now = datetime.now(timezone.utc)
    ev_id = uuid4()
    proj_id = uuid4()
    corr_id = uuid4()

    event = WebSocketEventV2(
        type="CHANGE_LOGGED",
        event_id=ev_id,
        project_id=proj_id,
        sequence_number=1,
        correlation_id=corr_id,
        occurred_at=now,
        actor=WebSocketActorV2(display_name="Test User"),
        payload={"sample": "data"},
    )
    assert event.type == "CHANGE_LOGGED"

    with pytest.raises(ValidationError):
        WebSocketEventV2(
            type="EVENTO_INEXISTENTE",
            event_id=ev_id,
            project_id=proj_id,
            sequence_number=1,
            correlation_id=corr_id,
            occurred_at=now,
            actor=WebSocketActorV2(display_name="Test User"),
            payload={},
        )


def test_build_summary_formatting():
    assert build_summary("CREATE_CLASS", {"name": "Producto"}) == "Creó la clase Producto"
    assert build_summary("DELETE_CLASS", {"class_name": "Factura"}) == "Eliminó la clase Factura"
    assert build_summary("CREATE_PROJECT_VERSION", {}) == "Guardó una versión"


def test_class_name_uniqueness_check():
    mock_db = MagicMock()
    service = UmlService(mock_db)

    diagram_id = uuid4()
    existing_cls = MagicMock()
    existing_cls.id = uuid4()
    existing_cls.name = "Producto"

    service.uml = MagicMock()
    service.uml.list_classes.return_value = [existing_cls]

    # Nombre repetido exacto
    with pytest.raises(HTTPException) as exc_info:
        service._ensure_unique_class_name(diagram_id, "Producto")
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "CLASS_NAME_DUPLICATED"

    # Nombre repetido con mayúsculas/minúsculas y espacios
    with pytest.raises(HTTPException) as exc_info:
        service._ensure_unique_class_name(diagram_id, "  pRoDuCtO  ")
    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["code"] == "CLASS_NAME_DUPLICATED"

    # Mismo id al actualizar no debe lanzar error
    service._ensure_unique_class_name(diagram_id, "producto", exclude_id=existing_cls.id)

    # Nombre diferente no debe lanzar error
    service._ensure_unique_class_name(diagram_id, "Cliente")
