from dataclasses import dataclass, field


@dataclass(frozen=True)
class JavaField:
    name: str
    java_type: str
    required: bool = False
    email: bool = False


@dataclass(frozen=True)
class JavaEntity:
    name: str
    package_name: str
    fields: list[JavaField] = field(default_factory=list)


@dataclass(frozen=True)
class JavaRelationship:
    owner: str
    target: str
    relationship_type: str
    annotation: str
    label: str | None = None
    source: str | None = None
    target_multiplicity: str | None = None
    source_multiplicity: str | None = None


@dataclass(frozen=True)
class SpringBootProject:
    name: str
    group_id: str
    artifact_id: str
    base_package: str
    entities: list[JavaEntity]
    relationships: list[JavaRelationship]


TYPE_MAPPING = {
    "string": "String",
    "str": "String",
    "char": "String",
    "character": "String",
    "text": "String",
    "integer": "Integer",
    "int": "Integer",
    "long": "Long",
    "uuid": "UUID",
    "double": "Double",
    "float": "Double",
    "boolean": "Boolean",
    "bool": "Boolean",
    "date": "LocalDate",
    "datetime": "LocalDateTime",
}


def to_pascal_case(value: str) -> str:
    parts = [part for part in value.replace("_", " ").replace("-", " ").split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Entidad"


def to_camel_case(value: str) -> str:
    pascal = to_pascal_case(value)
    return pascal[:1].lower() + pascal[1:]


def to_kebab_case(value: str) -> str:
    return "-".join(value.replace("_", " ").split()).lower() or "generated-backend"


def map_java_type(raw_type: str | None) -> str:
    if not raw_type:
        return "String"
    return TYPE_MAPPING.get(raw_type.lower(), to_pascal_case(raw_type))


def _is_many(multiplicity: str | None) -> bool:
    value = (multiplicity or "").strip().lower()
    return "*" in value or value.endswith("n") or value in {"many", "m"}


def _association_class_id(relation: dict) -> str | None:
    metadata = relation.get("metadata_json") if isinstance(relation.get("metadata_json"), dict) else {}
    raw = metadata.get("association_class_id") or relation.get("association_class_id")
    return str(raw) if raw else None


def analyze_model(intermediate_model: dict, name: str) -> SpringBootProject:
    base_package = f"com.caseinteligente.generated.{to_camel_case(name).lower()}"
    entities: list[JavaEntity] = []
    class_by_id: dict[str, str] = {}
    for item in intermediate_model.get("classes", []):
        entity_name = to_pascal_case(str(item.get("name", "Entidad")))
        class_by_id[str(item.get("id", entity_name))] = entity_name
        raw_fields = item.get("attributes", []) or []
        fields = [
            JavaField(
                name=to_camel_case(str(field.get("name", "campo"))),
                java_type=map_java_type(str(field.get("data_type", "String"))),
                required=bool(field.get("is_required", False)),
                email="correo" in str(field.get("name", "")).lower() or "email" in str(field.get("name", "")).lower(),
            )
            for field in raw_fields
            if str(field.get("name", "")).lower() != "id"
        ]
        if not fields:
            fields = [JavaField(name="nombre", java_type="String", required=True)]
        entities.append(JavaEntity(name=entity_name, package_name=base_package, fields=fields))

    relationships = []
    for relation in intermediate_model.get("relationships", []):
        source = class_by_id.get(
            str(relation.get("source_class_id")),
            str(relation.get("source") or relation.get("source_class_id", "")),
        )
        target = class_by_id.get(
            str(relation.get("target_class_id")),
            str(relation.get("target") or relation.get("target_class_id", "")),
        )
        if not source or not target:
            continue
        relation_type = str(relation.get("type") or relation.get("relationship_type") or "association")
        if relation_type in {"inheritance", "implementation", "dependency"}:
            continue

        association_class_id = _association_class_id(relation)
        association_class = class_by_id.get(association_class_id or "")
        if association_class:
            for endpoint in (source, target):
                relationships.append(
                    JavaRelationship(
                        owner=to_pascal_case(association_class),
                        source=to_pascal_case(association_class),
                        target=to_pascal_case(endpoint),
                        relationship_type="association_class",
                        annotation="ManyToOne",
                        label=relation.get("label"),
                        source_multiplicity=relation.get("source_cardinality"),
                        target_multiplicity=relation.get("target_cardinality"),
                    )
                )
            continue

        source_multiplicity = relation.get("source_cardinality")
        target_multiplicity = relation.get("target_cardinality")
        if _is_many(target_multiplicity) and not _is_many(source_multiplicity):
            owner, related = target, source
        else:
            owner, related = source, target
        relationships.append(
            JavaRelationship(
                owner=to_pascal_case(owner),
                source=to_pascal_case(source),
                target=to_pascal_case(related),
                relationship_type=relation_type,
                annotation="ManyToOne",
                label=relation.get("label"),
                source_multiplicity=source_multiplicity,
                target_multiplicity=target_multiplicity,
            )
        )

    return SpringBootProject(
        name=to_pascal_case(name),
        group_id="com.caseinteligente.generated",
        artifact_id=to_kebab_case(name),
        base_package=base_package,
        entities=entities,
        relationships=relationships,
    )
