from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.modules.generacion_software.coordinated_generator.contracts.generation_plan import (
    GenerationPlan,
)


class ManifestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class UiManifestField(ManifestModel):
    id: str
    name: str
    label: str
    control: str
    required: bool
    logical_type: str


class UiManifestAction(ManifestModel):
    id: str
    label: str
    interaction: str
    placement: str
    confirmation_required: bool = False
    icon: str = "play"


class UiManifestScreen(ManifestModel):
    id: str
    kind: Literal["list", "detail", "form", "filter", "action"]
    title: str
    fields: tuple[UiManifestField, ...] = ()
    actions: tuple[UiManifestAction, ...] = ()


class UiManifestModule(ManifestModel):
    id: str
    name: str
    label: str
    icon: str = "folder"
    screens: tuple[UiManifestScreen, ...] = ()


class UiManifest(ManifestModel):
    schema_version: Literal[1] = 1
    source_hash: str
    source_transformation_id: str | None = None
    modules: tuple[UiManifestModule, ...]
    supported_states: tuple[str, ...] = (
        "content", "loading", "empty", "error", "offline", "unauthorized", "success"
    )
    diagnostics: tuple[dict, ...] = ()


def build_ui_manifest(plan: GenerationPlan) -> UiManifest:
    action_map: dict[str, list[UiManifestAction]] = {}
    action_screens: dict[str, list[UiManifestScreen]] = {}
    for action in plan.ui_actions:
        manifest_action = UiManifestAction(
            id=action.operation_id, label=action.label, interaction=action.interaction,
            placement=action.placement or "detail", confirmation_required=action.confirmation_required,
            icon="play",
        )
        action_map.setdefault(action.owner_module, []).append(manifest_action)
        action_screens.setdefault(action.owner_module, []).append(UiManifestScreen(
            id=f"{action.owner_module}-action-{action.operation_id}", kind="action", title=action.label,
            fields=tuple(UiManifestField(
                id=item.parameter_id, name=item.json_name, label=item.label,
                control=item.control, required=item.required,
                logical_type=item.logical_type.logical,
            ) for item in action.fields if not item.hidden),
            actions=(manifest_action,),
        ))
    modules = []
    for entity in plan.entities:
        fields = tuple(UiManifestField(
            id=item.id or f"{entity.id}-{item.json_name}", name=item.json_name,
            label=item.source_name.replace("_", " ").strip().capitalize(),
            control=_control(item.logical_type.logical), required=item.required,
            logical_type=item.logical_type.logical,
        ) for item in entity.fields)
        actions = tuple(action_map.get(entity.module_name, []))
        screens = (
            UiManifestScreen(id=f"{entity.module_name}-list", kind="list", title=entity.source_name, fields=fields, actions=actions),
            UiManifestScreen(id=f"{entity.module_name}-detail", kind="detail", title=f"Detalle {entity.source_name}", fields=fields, actions=actions),
            UiManifestScreen(id=f"{entity.module_name}-form", kind="form", title=f"Formulario {entity.source_name}", fields=fields, actions=actions),
            UiManifestScreen(id=f"{entity.module_name}-filter", kind="filter", title=f"Filtrar {entity.source_name}", fields=fields),
            *tuple(action_screens.get(entity.module_name, [])),
        )
        modules.append(UiManifestModule(id=entity.id, name=entity.module_name, label=entity.source_name, screens=screens))
    return UiManifest(source_hash=plan.canonical_hash,
        source_transformation_id=plan.source_transformation_id, modules=tuple(modules),
        diagnostics=tuple(item.model_dump(mode="json") for item in plan.diagnostics))


def _control(logical: str) -> str:
    return {
        "boolean": "switch", "date": "date_picker", "datetime": "date_time_picker",
        "integer": "number_input", "decimal": "decimal_input", "entity_id": "entity_selector",
    }.get(logical, "text_input")
