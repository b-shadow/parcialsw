from dataclasses import dataclass, field


@dataclass(frozen=True)
class DartField:
    name: str
    dart_type: str
    required: bool = False
    input_type: str = "text"


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


def analyze_uml_for_flutter(
    intermediate_model: dict,
    name: str,
    api_base_url: str = "http://localhost:8080",
) -> FlutterProject:
    entities: list[DartEntity] = []
    for item in intermediate_model.get("classes", []):
        entity_name = to_pascal_case(str(item.get("name", "Entidad")))
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
        entities.append(DartEntity(name=entity_name, module_name=to_snake_case(entity_name), fields=fields))
    return FlutterProject(
        name=to_pascal_case(name),
        package_name=to_package_name(name),
        entities=entities,
        api_base_url=api_base_url,
    )
