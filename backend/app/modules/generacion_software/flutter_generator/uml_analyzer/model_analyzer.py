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
    return "*" in value or value.endswith("n") or value in {"many", "m"}


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


def analyze_uml_for_flutter(
    intermediate_model: dict,
    name: str,
    api_base_url: str = "http://localhost:8080",
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
    )
