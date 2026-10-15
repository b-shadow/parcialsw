import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DartField:
    name: str
    dart_type: str
    required: bool = False
    input_type: str = "text"
    relation_target: str | None = None
    relation_module: str | None = None


@dataclass(frozen=True)
class DartEntity:
    name: str
    module_name: str
    fields: list[DartField] = field(default_factory=list)


@dataclass(frozen=True)
class FlutterProject:
    name: str
    package_name: str
    entities: list[DartEntity]
    api_base_url: str
    theme_config: "FlutterThemeConfig"


@dataclass(frozen=True)
class FlutterThemeConfig:
    primary_color: str = "#0F766E"
    secondary_color: str = "#14B8A6"
    background_color: str = "#F8FAFC"
    surface_color: str = "#FFFFFF"
    button_color: str = "#0F766E"
    font_family: str = "Roboto"
    border_radius: int = 12
    button_style: str = "filled"
    density: str = "normal"


TYPE_MAPPING = {
    "string": "String",
    "str": "String",
    "integer": "int",
    "int": "int",
    "long": "int",
    "uuid": "String",
    "double": "double",
    "float": "double",
    "boolean": "bool",
    "bool": "bool",
    "date": "DateTime",
    "datetime": "DateTime",
}


def to_pascal_case(value: str) -> str:
    parts = [part for part in value.replace("_", " ").replace("-", " ").split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Entidad"


def to_camel_case(value: str) -> str:
    pascal = to_pascal_case(value)
    return pascal[:1].lower() + pascal[1:]


def to_snake_case(value: str) -> str:
    chars: list[str] = []
    for index, char in enumerate(to_pascal_case(value)):
        if char.isupper() and index > 0:
            chars.append("_")
        chars.append(char.lower())
    return "".join(chars) or "entidad"


def to_package_name(value: str) -> str:
    return to_snake_case(value).replace("__", "_")


def map_dart_type(raw_type: str | None) -> str:
    if not raw_type:
        return "String"
    return TYPE_MAPPING.get(raw_type.lower(), "String")


def _safe_hex(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text if re.fullmatch(r"#[0-9A-Fa-f]{6}", text) else fallback


def _safe_choice(value: object, fallback: str, allowed: set[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in allowed else fallback


def _safe_border_radius(value: object, fallback: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return fallback
    return min(32, max(0, numeric))


def normalize_theme_config(raw_theme: dict | None = None) -> FlutterThemeConfig:
    if not raw_theme:
        return FlutterThemeConfig()
    defaults = FlutterThemeConfig()
    return FlutterThemeConfig(
        primary_color=_safe_hex(raw_theme.get("primary_color"), defaults.primary_color),
        secondary_color=_safe_hex(raw_theme.get("secondary_color"), defaults.secondary_color),
        background_color=_safe_hex(raw_theme.get("background_color"), defaults.background_color),
        surface_color=_safe_hex(raw_theme.get("surface_color"), defaults.surface_color),
        button_color=_safe_hex(raw_theme.get("button_color"), defaults.button_color),
        font_family=str(raw_theme.get("font_family") or defaults.font_family).strip()[:80] or defaults.font_family,
        border_radius=_safe_border_radius(raw_theme.get("border_radius"), defaults.border_radius),
        button_style=_safe_choice(raw_theme.get("button_style"), defaults.button_style, {"filled", "outline", "tonal"}),
        density=_safe_choice(raw_theme.get("density"), defaults.density, {"compact", "normal", "comfortable"}),
    )


def input_type_for(field_name: str, dart_type: str) -> str:
    normalized = field_name.lower()
    if dart_type == "bool":
        return "switch"
    if dart_type == "DateTime":
        return "date"
    if dart_type in {"int", "double"}:
        return "number"
    if "correo" in normalized or "email" in normalized:
        return "email"
    return "text"


def _is_many(multiplicity: str | None) -> bool:
    value = (multiplicity or "").strip().lower()
    return (
        "*" in value
        or value.endswith("n")
        or value in {"many", "m", "muchos", "muchas", "varios", "varias"}
    )


def _association_class_id(relation: dict) -> str | None:
    metadata = relation.get("metadata_json") if isinstance(relation.get("metadata_json"), dict) else {}
    raw = metadata.get("association_class_id") or relation.get("association_class_id")
    return str(raw) if raw else None


def _relation_field(target_entity: str) -> DartField:
    return DartField(
        name=f"{to_camel_case(target_entity)}Id",
        dart_type="String",
        input_type="relation",
        relation_target=to_pascal_case(target_entity),
        relation_module=to_snake_case(target_entity),
    )


def _join_entity_name(source: str, target: str, existing_names: set[str]) -> str:
    base_name = f"{to_pascal_case(source)}{to_pascal_case(target)}"
    if base_name not in existing_names:
        return base_name
    fallback_name = f"{base_name}Relacion"
    suffix = 2
    candidate = fallback_name
    while candidate in existing_names:
        candidate = f"{fallback_name}{suffix}"
        suffix += 1
    return candidate


def analyze_uml_for_flutter(
    intermediate_model: dict,
    name: str,
    api_base_url: str = "http://localhost:8080",
    theme_config: dict | None = None,
) -> FlutterProject:
    entities_by_name: dict[str, DartEntity] = {}
    class_by_id: dict[str, str] = {}
    for item in intermediate_model.get("classes", []):
        entity_name = to_pascal_case(str(item.get("name", "Entidad")))
        class_by_id[str(item.get("id", entity_name))] = entity_name
        fields = []
        for raw_field in item.get("attributes", []) or []:
            raw_name = str(raw_field.get("name", "campo"))
            if raw_name.lower() == "id":
                continue
            dart_type = map_dart_type(str(raw_field.get("data_type", "String")))
            field_name = to_camel_case(raw_name)
            fields.append(
                DartField(
                    name=field_name,
                    dart_type=dart_type,
                    required=bool(raw_field.get("is_required", False)),
                    input_type=input_type_for(field_name, dart_type),
                )
            )
        if not fields:
            fields = [DartField(name="nombre", dart_type="String", required=True)]
        entities_by_name[entity_name] = DartEntity(name=entity_name, module_name=to_snake_case(entity_name), fields=fields)

    for relation in intermediate_model.get("relationships", []) or []:
        source = class_by_id.get(
            str(relation.get("source_class_id")),
            to_pascal_case(str(relation.get("source") or relation.get("source_class_id", ""))),
        )
        target = class_by_id.get(
            str(relation.get("target_class_id")),
            to_pascal_case(str(relation.get("target") or relation.get("target_class_id", ""))),
        )
        relation_type = str(relation.get("type") or relation.get("relationship_type") or "association")
        if not source or not target or relation_type in {"inheritance", "implementation", "dependency"}:
            continue

        association_class = class_by_id.get(_association_class_id(relation) or "")
        if association_class and association_class in entities_by_name:
            entity = entities_by_name[association_class]
            relation_fields = [_relation_field(source), _relation_field(target)]
            existing = {field.name for field in entity.fields}
            entities_by_name[association_class] = DartEntity(
                name=entity.name,
                module_name=entity.module_name,
                fields=[*entity.fields, *[field for field in relation_fields if field.name not in existing]],
            )
            continue

        source_multiplicity = relation.get("source_cardinality")
        target_multiplicity = relation.get("target_cardinality")
        source_is_many = _is_many(source_multiplicity)
        target_is_many = _is_many(target_multiplicity)
        if source_is_many and target_is_many:
            existing_names = set(entities_by_name)
            join_entity = _join_entity_name(source, target, existing_names)
            relation_fields = [_relation_field(source), _relation_field(target)]
            entities_by_name[join_entity] = DartEntity(
                name=join_entity,
                module_name=to_snake_case(join_entity),
                fields=relation_fields,
            )
            continue

        owner = target if _is_many(target_multiplicity) and not _is_many(source_multiplicity) else source
        related = source if owner == target else target
        if owner in entities_by_name:
            entity = entities_by_name[owner]
            relation_field = _relation_field(related)
            if relation_field.name not in {field.name for field in entity.fields}:
                entities_by_name[owner] = DartEntity(
                    name=entity.name,
                    module_name=entity.module_name,
                    fields=[*entity.fields, relation_field],
                )

    entities = list(entities_by_name.values())
    return FlutterProject(
        name=to_pascal_case(name),
        package_name=to_package_name(name),
        entities=entities,
        api_base_url=api_base_url,
        theme_config=normalize_theme_config(theme_config),
    )
