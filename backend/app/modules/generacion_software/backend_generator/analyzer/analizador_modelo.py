from dataclasses import dataclass, field


@dataclass(frozen=True)
class CampoJava:
    name: str
    java_type: str
    required: bool = False
    email: bool = False


@dataclass(frozen=True)
class EntidadJava:
    name: str
    package_name: str
    fields: list[CampoJava] = field(default_factory=list)


@dataclass(frozen=True)
class RelacionJava:
    owner: str
    target: str
    relationship_type: str
    annotation: str
    label: str | None = None
    source: str | None = None
    target_multiplicity: str | None = None
    source_multiplicity: str | None = None


@dataclass(frozen=True)
class ProyectoSpringBoot:
    name: str
    group_id: str
    artifact_id: str
    base_package: str
    entities: list[EntidadJava]
    relationships: list[RelacionJava]


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


def a_pascal_case(value: str) -> str:
    parts = [part for part in value.replace("_", " ").replace("-", " ").split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Entidad"


def a_camel_case(value: str) -> str:
    pascal = a_pascal_case(value)
    return pascal[:1].lower() + pascal[1:]


def a_kebab_case(value: str) -> str:
    return "-".join(value.replace("_", " ").split()).lower() or "generated-backend"


def mapear_tipo_java(raw_type: str | None) -> str:
    if not raw_type:
        return "String"
    return TYPE_MAPPING.get(raw_type.lower(), a_pascal_case(raw_type))


def _is_many(multiplicity: str | None) -> bool:
    value = (multiplicity or "").strip().lower()
    return (
        "*" in value
        or value.endswith("n")
        or value in {"many", "m", "muchos", "muchas", "varios", "varias"}
    )


def _id_clase_asociativa(relation: dict) -> str | None:
    metadata = relation.get("metadata_json") if isinstance(relation.get("metadata_json"), dict) else {}
    raw = metadata.get("association_class_id") or relation.get("association_class_id")
    return str(raw) if raw else None


def _nombre_entidad_union(source: str, target: str, existing_names: set[str]) -> str:
    base_name = f"{a_pascal_case(source)}{a_pascal_case(target)}"
    if base_name not in existing_names:
        return base_name
    fallback_name = f"{base_name}Relacion"
    suffix = 2
    candidate = fallback_name
    while candidate in existing_names:
        candidate = f"{fallback_name}{suffix}"
        suffix += 1
    return candidate


def analizar_modelo(intermediate_model: dict, name: str) -> ProyectoSpringBoot:
    base_package = f"com.caseinteligente.generated.{a_camel_case(name).lower()}"
    entities: list[EntidadJava] = []
    class_by_id: dict[str, str] = {}
    for item in intermediate_model.get("classes", []):
        entity_name = a_pascal_case(str(item.get("name", "Entidad")))
        class_by_id[str(item.get("id", entity_name))] = entity_name
        raw_fields = item.get("attributes", []) or []
        fields = [
            CampoJava(
                name=a_camel_case(str(field.get("name", "campo"))),
                java_type=mapear_tipo_java(str(field.get("data_type", "String"))),
                required=bool(field.get("is_required", False)),
                email="correo" in str(field.get("name", "")).lower() or "email" in str(field.get("name", "")).lower(),
            )
            for field in raw_fields
            if str(field.get("name", "")).lower() != "id"
        ]
        if not fields:
            fields = [CampoJava(name="nombre", java_type="String", required=True)]
        entities.append(EntidadJava(name=entity_name, package_name=base_package, fields=fields))

    relationships = []
    entity_names = {entity.name for entity in entities}
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

        association_class_id = _id_clase_asociativa(relation)
        association_class = class_by_id.get(association_class_id or "")
        if association_class:
            for endpoint in (source, target):
                relationships.append(
                    RelacionJava(
                        owner=a_pascal_case(association_class),
                        source=a_pascal_case(association_class),
                        target=a_pascal_case(endpoint),
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
        source_is_many = _is_many(source_multiplicity)
        target_is_many = _is_many(target_multiplicity)
        if source_is_many and target_is_many:
            join_entity = _nombre_entidad_union(source, target, entity_names)
            if join_entity not in entity_names:
                entities.append(EntidadJava(name=join_entity, package_name=base_package, fields=[]))
                entity_names.add(join_entity)
            for endpoint in (source, target):
                relationships.append(
                    RelacionJava(
                        owner=join_entity,
                        source=join_entity,
                        target=a_pascal_case(endpoint),
                        relationship_type="implicit_join",
                        annotation="ManyToOne",
                        label=relation.get("label"),
                        source_multiplicity=source_multiplicity,
                        target_multiplicity=target_multiplicity,
                    )
                )
            continue

        if _is_many(target_multiplicity) and not _is_many(source_multiplicity):
            owner, related = target, source
        else:
            owner, related = source, target
        relationships.append(
            RelacionJava(
                owner=a_pascal_case(owner),
                source=a_pascal_case(source),
                target=a_pascal_case(related),
                relationship_type=relation_type,
                annotation="ManyToOne",
                label=relation.get("label"),
                source_multiplicity=source_multiplicity,
                target_multiplicity=target_multiplicity,
            )
        )

    return ProyectoSpringBoot(
        name=a_pascal_case(name),
        group_id="com.caseinteligente.generated",
        artifact_id=a_kebab_case(name),
        base_package=base_package,
        entities=entities,
        relationships=relationships,
    )
